# SPDX-License-Identifier: Apache-2.0
"""CPU checks for the isolated AMD port; no device or model qualification."""
import os
from pathlib import Path
from types import SimpleNamespace as NS
import pytest
import torch
from safetensors import safe_open
from safetensors.torch import save_file
import vllm.platforms as platforms
from vllm.platforms.cpu import CpuPlatform
platforms._current_platform = CpuPlatform()
from vllm import envs
from vllm.config.engram import EngramConfig
from vllm.models.qwen4_exp.common import file_gather as fg
from vllm.models.qwen4_exp.common.ngram_embedding import (
    Qwen4ExpPLEEmbedding, Qwen4ExpPLEUnquantizedEmbeddingMethod,
)
from vllm.models.qwen4_exp.amd import ple_layer as amd
from vllm.models.qwen4_exp.amd import model_state as state

@pytest.fixture(autouse=True)
def no_gpu_initialization():
    assert not torch.cuda.is_initialized()
    yield
    assert not torch.cuda.is_initialized()

@pytest.fixture
def make_reader(monkeypatch, tmp_path):
    # Distributed weight allocation is outside this CPU suite. All reader,
    # shard validation, offset discovery, preadv, staging and forward code is real.
    def base_init(self, num_embeddings, embedding_dim, *, params_dtype, **kw):
        torch.nn.Module.__init__(self)
        self.org_vocab_size = num_embeddings
        self.embedding_dim = embedding_dim
        self.params_dtype = params_dtype
        self.weight = torch.nn.Parameter(
            self.allocate_embedding_weight(num_embeddings, embedding_dim, params_dtype),
            requires_grad=False,
        )
    monkeypatch.setattr(Qwen4ExpPLEEmbedding, '__init__', base_init)
    cfg = NS(load_config=NS(load_format='safetensors'))
    monkeypatch.setattr(fg, 'get_current_vllm_config', lambda: cfg)
    readers=[]
    def create(dtype=torch.bfloat16, dummy=False, bind=True, symlink=False):
        cfg.load_config.load_format = 'dummy' if dummy else 'safetensors'
        reader=fg.Qwen4ExpPLEFileGatherEmbedding(
            8,4,params_dtype=dtype,padding_size=1,prefix='ple',
            embedding_method=None,num_ngram_heads=2,max_total_tokens=6,
        )
        readers.append(reader)
        reference=torch.arange(32,dtype=torch.float32).reshape(8,4).to(dtype)
        paths=[]
        if not dummy:
            for index in range(2):
                path=tmp_path/f'{len(readers)}-{index}.safetensors'
                save_file({'weight': reference[index*4:(index+1)*4]},str(path))
                paths.append(path)
                source=path
                if symlink:
                    source=tmp_path/f'link-{len(readers)}-{index}'
                    source.symlink_to(path)
                with safe_open(str(source),framework='pt',device='cpu') as handle:
                    reader.accept_checkpoint_shard(index,handle.get_tensor('weight'),4)
        if bind:
            reader.bind_file_shards()
        return reader,reference,paths
    yield create
    for reader in readers:reader.close()

@pytest.mark.parametrize('dtype',[torch.bfloat16,torch.float32,torch.float8_e4m3fn])
@pytest.mark.parametrize('symlink',[False,True])
def test_real_safetensor_rows_match_bytes_and_duplicate_order(make_reader,dtype,symlink):
    reader,reference,_=make_reader(dtype,symlink=symlink)
    ids=torch.tensor([[7,0],[3,4],[7,1]])
    reader._host_ids[:3].copy_(ids);reader.stage_rows(3)
    expected=reference.view(torch.uint8)[ids].reshape(3,-1)
    assert torch.equal(reader(torch.zeros(3)).view(torch.uint8),expected)
    assert reader.weight.numel()==0
    assert reader._fds_t.device.type=='cpu'
    assert reader._shards=={}

def test_file_descriptors_are_read_only_and_closed(make_reader):
    import fcntl
    reader,_,_=make_reader();fds=list(reader._fds.values())
    assert all(fcntl.fcntl(fd,fcntl.F_GETFL)&os.O_ACCMODE==os.O_RDONLY for fd in fds)
    reader.close()
    for fd in fds:
        with pytest.raises(OSError):os.fstat(fd)

def test_rename_unlink_after_binding_keeps_owned_readonly_descriptors(make_reader):
    reader,reference,paths=make_reader()
    for p in paths:p.unlink()
    reader._host_ids[0].copy_(torch.tensor([0,7]));reader.stage_rows(1)
    assert torch.equal(reader(torch.zeros(1)),reference[[0,7]].reshape(1,-1))

@pytest.mark.parametrize('ids',[[-1,0],[8,0],[0,100]])
def test_bad_ids_fail_without_publishing_partial_staging(make_reader,ids):
    reader,_,_=make_reader();reader._staging.fill_(9);before=reader._staging.clone()
    reader._host_ids[0].copy_(torch.tensor(ids))
    with pytest.raises(IndexError):reader.stage_rows(1)
    assert torch.equal(reader._staging,before)

def test_truncation_fails_without_publishing_partial_staging(make_reader):
    reader,_,paths=make_reader();reader._staging.fill_(9);before=reader._staging.clone()
    paths[-1].write_bytes(b'')
    reader._host_ids[0].copy_(torch.tensor([0,7]))
    with pytest.raises(ValueError,match='truncated'):reader.stage_rows(1)
    assert torch.equal(reader._staging,before)

def test_heap_backed_shards_are_rejected(make_reader):
    reader,reference,_=make_reader(bind=False)
    reader._shards={}
    reader.accept_checkpoint_shard(0,reference[:4].clone(),4)
    reader.accept_checkpoint_shard(1,reference[4:].clone(),4)
    with pytest.raises(ValueError,match='file-backed'):reader.bind_file_shards()

def test_missing_shard_is_rejected(make_reader):
    reader,_,_=make_reader(bind=False);reader._shards.pop(1)
    with pytest.raises(ValueError,match='cover'):reader.bind_file_shards()

def test_duplicate_shard_is_rejected(make_reader):
    reader,reference,_=make_reader(bind=False)
    with pytest.raises(ValueError,match='Duplicate'):reader.accept_checkpoint_shard(0,reference[:4],4)

def test_reload_poisoning_stops_future_staging(make_reader):
    reader,reference,_=make_reader()
    with pytest.raises(RuntimeError,match='reload'):reader.accept_checkpoint_shard(0,reference[:4],4)
    with pytest.raises(RuntimeError):reader.stage_rows(1)

@pytest.mark.parametrize('size',[-1,7])
def test_staging_capacity_is_bounded(make_reader,size):
    reader,_,_=make_reader()
    with pytest.raises(ValueError,match='capacity'):reader.stage_rows(size)

def test_dummy_profile_is_zero_only_and_forward_has_no_io(make_reader,monkeypatch):
    reader,_,_=make_reader(dummy=True);reader._host_ids[:2].zero_();reader.stage_rows(2)
    def forbidden(*a,**k):raise AssertionError('I/O reached captured forward')
    monkeypatch.setattr(os,'preadv',forbidden)
    result=reader(torch.zeros(2))
    assert result.data_ptr()==reader._staging.data_ptr()
    assert torch.count_nonzero(result)==0
    assert reader.start_prefetch(None,None) is None

@pytest.mark.parametrize('rank',[0,1])
def test_actual_amd_forward_does_not_double_sum_tp2_rows(make_reader,monkeypatch,rank):
    reader,reference,_=make_reader();reader._host_ids[:2].copy_(torch.tensor([[0,1],[6,7]]));reader.stage_rows(2)
    obj=amd.Qwen4ExpNGramEmbedding.__new__(amd.Qwen4ExpNGramEmbedding)
    torch.nn.Module.__init__(obj);obj.ngram_embedding=reader;obj.use_sequence_parallel=True
    monkeypatch.setattr(amd,'sp_shard',lambda x:x.chunk(2,dim=0)[rank])
    def forbidden(*a,**k):raise AssertionError('Full rows must not be reduce-scattered')
    obj._sp_shard_embeddings=forbidden
    result=obj(torch.zeros(2,dtype=torch.long),None,None)
    expected=reference[[0,1] if rank==0 else [6,7]].reshape(1,-1)
    assert torch.equal(result,expected)

def test_loader_binds_after_all_weights_via_real_quantization_hook(make_reader):
    reader,_,_=make_reader(bind=False)
    Qwen4ExpPLEUnquantizedEmbeddingMethod().process_weights_after_loading(reader)
    assert reader._bound and reader._shards=={}

@pytest.mark.parametrize('key',['dp_shared_memory','use_thp','embedding_across_dp'])
def test_config_rejects_incompatible_table_modes(key):
    with pytest.raises(ValueError):EngramConfig(rocm_host_file_gather=True,**{key:True})

@pytest.mark.parametrize('tp,dp,pp,elastic',[(3,1,1,False),(2,2,1,False),(2,1,2,False),(2,1,1,True)])
def test_config_rejects_unsupported_topology(tp,dp,pp,elastic):
    cfg=EngramConfig(rocm_host_file_gather=True)
    with pytest.raises(ValueError):cfg.verify_parallel_config(NS(tensor_parallel_size=tp,data_parallel_size=dp,pipeline_parallel_size=pp,enable_elastic_ep=elastic))

@pytest.mark.parametrize('tp',[1,2])
def test_config_accepts_only_explicit_rocm_v2_qwen_path(monkeypatch,tp):
    monkeypatch.setattr(platforms,'_current_platform',NS(is_rocm=lambda:True))
    monkeypatch.setattr(envs,'VLLM_USE_V2_MODEL_RUNNER',True,raising=False)
    cfg=EngramConfig(rocm_host_file_gather=True)
    cfg.verify_model_config(NS(architecture='Qwen4ExpForCausalLM',hf_text_config=NS(ple_layer_ids=[0])))
    parallel=NS(tensor_parallel_size=tp,data_parallel_size=1,pipeline_parallel_size=1,enable_elastic_ep=False)
    cfg.resolve_dp_shared_memory(parallel);cfg.verify_parallel_config(parallel)
    assert cfg.dp_shared_memory is False
    assert cfg.compute_hash()!=EngramConfig().compute_hash()

def test_non_rocm_platform_and_implicit_runner_are_rejected(monkeypatch):
    model=NS(architecture='Qwen4ExpForCausalLM',hf_text_config=NS(ple_layer_ids=[0]));cfg=EngramConfig(rocm_host_file_gather=True)
    monkeypatch.setattr(platforms,'_current_platform',NS(is_rocm=lambda:False))
    with pytest.raises(ValueError,match='ROCm'):cfg.verify_model_config(model)
    monkeypatch.setattr(platforms,'_current_platform',NS(is_rocm=lambda:True))
    monkeypatch.setattr(envs,'VLLM_USE_V2_MODEL_RUNNER',None,raising=False)
    with pytest.raises(ValueError,match='V2_MODEL_RUNNER'):cfg.verify_model_config(model)

def test_real_input_hook_clears_stale_request_tail(monkeypatch):
    monkeypatch.setattr(state.MambaHybridModelState,'prepare_inputs',lambda *a:{})
    obj=state.Qwen4ExpModelState.__new__(state.Qwen4ExpModelState)
    obj.uses_ngram_embedding=True;obj.file_gather_modules=[NS(ngram_embedding=NS(_staging=torch.ones(4,2,4)))]
    obj.ple_query_start_loc=torch.tensor([0,1,3,91,92],dtype=torch.int32)
    obj._prepare_ngram_context=lambda *a:torch.zeros(3,1,dtype=torch.int32)
    seen=[];monkeypatch.setattr(state,'stage_checkpoint_rows',lambda mods,ids,q,c:seen.append(q.clone()))
    batch=NS(num_tokens=2,num_tokens_after_padding=4,num_reqs_after_padding=1,query_start_loc=torch.tensor([0,2],dtype=torch.int32),input_ids=torch.tensor([4,5]))
    result=obj.prepare_inputs(batch,None)
    assert seen[0].tolist()==[0,2,2,2,2]
    assert result['query_start_loc'].tolist()==[0,2]
    assert torch.count_nonzero(obj.file_gather_modules[0].ngram_embedding._staging[2:])==0

@pytest.mark.parametrize('rank',[0,1])
def test_real_base_constructor_keeps_tp2_table_storage_empty(monkeypatch,rank):
    from vllm.models.qwen4_exp.common import ngram_embedding as shared
    group=NS(world_size=2,rank_in_group=rank)
    monkeypatch.setattr(shared,'get_etp_group',lambda:group)
    monkeypatch.setattr(shared,'get_tp_group',lambda:group)
    monkeypatch.setattr(fg,'get_current_vllm_config',lambda:NS(load_config=NS(load_format='dummy')))
    reader=fg.Qwen4ExpPLEFileGatherEmbedding(
        8,4,params_dtype=torch.bfloat16,padding_size=2,prefix='ple',
        embedding_method=Qwen4ExpPLEUnquantizedEmbeddingMethod(),
        num_ngram_heads=2,max_total_tokens=3,reduce_results=False,
    )
    try:
        assert reader.tp_size==2 and reader.tp_rank==rank
        assert reader.weight.numel()==0 and reader._staging.shape==(3,2,4)
        reader.bind_file_shards();reader._host_ids.zero_();reader.stage_rows(2)
        assert reader.finalize_prefetch(2).data_ptr()==reader._staging.data_ptr()
    finally:reader.close()

def test_file_gather_context_capacity_tail_is_eos_not_stale():
    obj=state.Qwen4ExpModelState.__new__(state.Qwen4ExpModelState)
    obj.file_gather_modules=[object()];obj.ngram_eos_token_id=99
    obj.ngram_context=torch.tensor([[7],[8],[9],[10]],dtype=torch.int32)
    obj.ngram_context_offsets=torch.tensor([-1])
    batch=NS(num_reqs=1,num_reqs_after_padding=1,idx_mapping=torch.tensor([0]))
    requests=NS(num_computed_tokens=NS(gpu=torch.tensor([2])),all_token_ids=NS(gpu=torch.tensor([[3,4,5]])))
    context=obj._prepare_ngram_context(batch,requests)
    assert context.shape==(4,1) and context[:,0].tolist()==[4,99,99,99]

def test_fp8_scale_validation_precedes_file_binding():
    from vllm.models.qwen4_exp.common.ngram_embedding import Qwen4ExpPLEFp8EmbeddingMethod
    method=Qwen4ExpPLEFp8EmbeddingMethod.__new__(Qwen4ExpPLEFp8EmbeddingMethod)
    calls=[]
    layer=NS(weight_scale=torch.tensor(torch.finfo(torch.float32).min),bind_file_shards=lambda:calls.append(True))
    with pytest.raises(ValueError,match='global scale'):method.process_weights_after_loading(layer)
    assert calls==[]
    layer.weight_scale=torch.tensor(1.0);method.process_weights_after_loading(layer)
    assert calls==[True]

def test_model_state_rejects_unqualified_mtp_before_ngram_buffers(monkeypatch):
    def base(self,*a,**kw):self.model_config=NS(hf_text_config=NS(ple_layer_ids=[0]))
    monkeypatch.setattr(state.MambaHybridModelState,'__init__',base)
    embedding=fg.Qwen4ExpPLEFileGatherEmbedding.__new__(fg.Qwen4ExpPLEFileGatherEmbedding)
    torch.nn.Module.__init__(embedding)
    ng=amd.Qwen4ExpNGramEmbedding.__new__(amd.Qwen4ExpNGramEmbedding)
    torch.nn.Module.__init__(ng);ng.ngram_embedding=embedding
    with pytest.raises(ValueError,match='MTP off'):
        state.Qwen4ExpModelState(NS(speculative_config=object()),NS(modules=lambda:[ng]),None,torch.device('cpu'))
