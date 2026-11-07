"""Supervise the two ComfyUI ranks of the production H3 TP2 server.

Usage (from start-comfyui, inside guarded_comfy's owned scope):
  python tp2_pair.py <rank0 ComfyUI args...>
Rank 1 (Sapphire only, 127.0.0.1:18189, headless follower) starts first and blocks in the RCCL
rendezvous; rank 0 (both cards visible, the normal production server) follows. If either rank
exits, the other is stopped and the pair is restarted (at most 3 times in 10 minutes), so a lost
RCCL peer can never leave a half-pair serving H3.
"""
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
STATE = REPO / "graphics/generated"
FOLLOWER_PORT = 18189
RCCL_PORT = "29673"
RCCL_ENV = {  # qualified November 7 transport settings (direct P2P/IPC is selected automatically)
    "HSA_ENABLE_SDMA": "0", "NCCL_PROTO": "Simple", "NCCL_BUFFSIZE": "1048576",
    "NCCL_MIN_NCHANNELS": "1", "NCCL_MAX_NCHANNELS": "1",
    # INFO prints ~12k tuning lines per H3 job; set H3_TP2_NCCL_DEBUG=INFO to see "via P2P/IPC".
    "NCCL_DEBUG": os.environ.get("H3_TP2_NCCL_DEBUG", "WARN"),
    "ROCM_INT8_KITCHEN_PATCH": "off", "TP_WIRE": "bf16",
    "MASTER_ADDR": "127.0.0.1", "MASTER_PORT": RCCL_PORT,
    # pre-sliced per-rank H3 halves written by make_halves.py (manifest-checked by the glue)
    "H3_TP2_HALVES": os.environ.get("H3_TP2_HALVES", "<model drive>/Graphics-Models/experimental/h3-tp2-halves-20261107"),
}
FOLLOWER_ARGS = ["--listen", "127.0.0.1", "--port", str(FOLLOWER_PORT), "--reserve-vram", "2",
                 "--disable-pinned-memory", "--disable-async-offload", "--disable-dynamic-vram",
                 "--cache-none", "--use-ck-attention", "--disable-partner-nodes"]


def arg_value(args, name):
    return args[args.index(name) + 1] if name in args else None


def start(rank, args, devices):
    env = os.environ.copy()
    env.update(RCCL_ENV)
    env.pop("NCCL_P2P_DISABLE", None)
    env.update(TP_RANK=str(rank), ROCR_VISIBLE_DEVICES=devices)
    env.pop("HIP_VISIBLE_DEVICES", None)
    if rank == 0:
        env["H3_TP2_FOLLOWER"] = "http://127.0.0.1:%d" % FOLLOWER_PORT
    cmd = [sys.executable, str(HERE / "tp_boot.py")] + args
    if rank == 1:
        log = open(STATE / time.strftime("tp2-rank1-%Y%m%d-%H%M%S.log"), "w")
        return subprocess.Popen(cmd, env=env, cwd=os.environ["COMFY_ROOT"], stdout=log,
                                stderr=subprocess.STDOUT, start_new_session=False)
    return subprocess.Popen(cmd, env=env, cwd=os.environ["COMFY_ROOT"])


def stop(procs):
    for p in procs:
        if p.poll() is None:
            p.terminate()
    for p in procs:
        try:
            p.wait(timeout=20)
        except subprocess.TimeoutExpired:
            p.kill()
            p.wait()


def main():
    rank0_args = sys.argv[1:]
    devices = os.environ.get("H3_TP2_DEVICES", "0,1").split(",")  # physical PowerColor, Sapphire
    shared = []
    for flag in ("--extra-model-paths-config", "--input-directory", "--user-directory"):
        v = arg_value(rank0_args, flag)
        if v:
            shared += [flag, v]
    follower_out = STATE / "tp2-follower-output"
    follower_out.mkdir(parents=True, exist_ok=True)
    follower_args = FOLLOWER_ARGS + shared + ["--output-directory", str(follower_out)]
    restarts = []
    procs = []

    def on_signal(*_):
        stop(procs)
        sys.exit(130)

    for s in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(s, on_signal)
    while True:
        procs[:] = [start(1, follower_args, devices[1])]
        time.sleep(3)
        procs.append(start(0, rank0_args, ",".join(devices)))
        while all(p.poll() is None for p in procs):
            time.sleep(0.5)
        codes = [p.poll() for p in procs]
        print("[h3_tp2] rank exited (rank1=%s rank0=%s); stopping pair" % tuple(codes), flush=True)
        stop(procs)
        now = time.monotonic()
        restarts = [t for t in restarts if now - t < 600] + [now]
        if len(restarts) > 3:
            print("[h3_tp2] too many restarts; giving up", flush=True)
            return 1
        time.sleep(5)


if __name__ == "__main__":
    sys.exit(main())
