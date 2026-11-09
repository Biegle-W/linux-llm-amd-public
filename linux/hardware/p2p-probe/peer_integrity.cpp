// Two-card peer integrity probe (rebuilt November 9, 2026 from the November 7 log format;
// the original source was lost with an unreferenced work folder).
// Direct: a kernel on the source card reads and writes memory on the target card, then
// hipMemcpyPeer both ways; 3 patterns, 16 MiB. IPC: the owner exports a buffer, a child
// process on the other card opens it, verifies and rewrites it; the owner verifies.
// "local" mode: each card writes and verifies 3 patterns in its own memory.
// Prints "RESULT direct_integrity=true ipc_integrity=true directions=2" and exits 0 on success.
#include <hip/hip_runtime.h>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cstdint>
#include <string>
#include <unistd.h>
#include <sys/wait.h>
#define CK(x) do{hipError_t e_=(x);if(e_!=hipSuccess){fprintf(stderr,"HIP error %s at line %d\n",hipGetErrorString(e_),__LINE__);exit(2);}}while(0)
static const size_t BYTES=16u<<20, N=BYTES/4;
__host__ __device__ inline uint32_t pat(size_t i,uint32_t s){uint32_t x=(uint32_t)i*2654435761u^s;x^=x>>13;x*=0x5bd1e995u;x^=x>>15;return x;}
__global__ void fill(uint32_t*p,size_t n,uint32_t s){for(size_t i=blockIdx.x*(size_t)blockDim.x+threadIdx.x;i<n;i+=(size_t)gridDim.x*blockDim.x)p[i]=pat(i,s);}
__global__ void remote_rw(const uint32_t*rsrc,uint32_t*ldst,uint32_t*rdst,size_t n,uint32_t s2){for(size_t i=blockIdx.x*(size_t)blockDim.x+threadIdx.x;i<n;i+=(size_t)gridDim.x*blockDim.x){ldst[i]=rsrc[i];rdst[i]=pat(i,s2);}}
__global__ void verify(const uint32_t*p,size_t n,uint32_t s,unsigned long long*bad){for(size_t i=blockIdx.x*(size_t)blockDim.x+threadIdx.x;i<n;i+=(size_t)gridDim.x*blockDim.x)if(p[i]!=pat(i,s))atomicAdd(bad,1ull);}
static unsigned long long check(int dev,const uint32_t*p,uint32_t s){CK(hipSetDevice(dev));unsigned long long*b;CK(hipMalloc(&b,8));CK(hipMemset(b,0,8));verify<<<1024,256>>>(p,N,s,b);CK(hipGetLastError());CK(hipDeviceSynchronize());unsigned long long h=0;CK(hipMemcpy(&h,b,8,hipMemcpyDeviceToHost));CK(hipFree(b));return h;}
static void peer(int a,int b){CK(hipSetDevice(a));hipError_t e=hipDeviceEnablePeerAccess(b,0);if(e!=hipSuccess&&e!=hipErrorPeerAccessAlreadyEnabled){fprintf(stderr,"peer access %d->%d: %s\n",a,b,hipGetErrorString(e));exit(3);}(void)hipGetLastError();}
static bool direct(int src,int dst){
 uint32_t *rs,*rd,*l;CK(hipSetDevice(dst));CK(hipMalloc(&rs,BYTES));CK(hipMalloc(&rd,BYTES));CK(hipSetDevice(src));CK(hipMalloc(&l,BYTES));bool ok=true;
 for(uint32_t k=0;k<3;k++){uint32_t s=0x1000u*(k+1)+src*16+dst,s2=s^0xA5A5A5A5u,s3=s+0x777u;
  CK(hipSetDevice(dst));fill<<<1024,256>>>(rs,N,s);CK(hipDeviceSynchronize());
  CK(hipSetDevice(src));remote_rw<<<1024,256>>>(rs,l,rd,N,s2);CK(hipGetLastError());CK(hipDeviceSynchronize());
  ok&=check(src,l,s)==0;ok&=check(dst,rd,s2)==0;
  CK(hipSetDevice(dst));fill<<<1024,256>>>(rs,N,s3);CK(hipDeviceSynchronize());
  CK(hipMemcpyPeer(l,src,rs,dst,BYTES));CK(hipSetDevice(src));CK(hipDeviceSynchronize());ok&=check(src,l,s3)==0;
  CK(hipMemcpyPeer(rd,dst,l,src,BYTES));CK(hipSetDevice(dst));CK(hipDeviceSynchronize());ok&=check(dst,rd,s3)==0;}
 CK(hipSetDevice(dst));CK(hipFree(rs));CK(hipFree(rd));CK(hipSetDevice(src));CK(hipFree(l));
 printf("DIRECT source=%d target=%d patterns=3 bytes=%zu remote-read/write and peer-copy %s\n",src,dst,BYTES,ok?"PASS":"FAIL");fflush(stdout);return ok;}
static int child(int dev,int owner,const char*hex,uint32_t s,uint32_t s2){
 hipIpcMemHandle_t h;for(size_t i=0;i<sizeof(h);i++){unsigned v;sscanf(hex+2*i,"%2x",&v);((unsigned char*)&h)[i]=(unsigned char)v;}
 peer(dev,owner);CK(hipSetDevice(dev));void*p;CK(hipIpcOpenMemHandle(&p,h,hipIpcMemLazyEnablePeerAccess));
 bool ok=check(dev,(uint32_t*)p,s)==0;CK(hipSetDevice(dev));fill<<<1024,256>>>((uint32_t*)p,N,s2);CK(hipGetLastError());CK(hipDeviceSynchronize());ok&=check(dev,(uint32_t*)p,s2)==0;
 CK(hipIpcCloseMemHandle(p));printf("IPC child device=%d remote-read/write %s\n",dev,ok?"PASS":"FAIL");fflush(stdout);return ok?0:4;}
static bool ipc(const char*self,int owner,int acc){
 CK(hipSetDevice(owner));uint32_t*p;CK(hipMalloc(&p,BYTES));uint32_t s=0x5150u+owner,s2=s^0x3C3C3C3Cu;fill<<<1024,256>>>(p,N,s);CK(hipDeviceSynchronize());
 hipIpcMemHandle_t h;CK(hipIpcGetMemHandle(&h,p));char hex[2*sizeof(h)+1];for(size_t i=0;i<sizeof(h);i++)sprintf(hex+2*i,"%02x",((unsigned char*)&h)[i]);
 fflush(stdout);pid_t pid=fork();if(pid==0){std::string a=std::to_string(acc),o=std::to_string(owner),x=std::to_string(s),y=std::to_string(s2);execl(self,self,"--child",a.c_str(),o.c_str(),hex,x.c_str(),y.c_str(),(char*)0);_exit(5);}
 int st=0;waitpid(pid,&st,0);bool ok=WIFEXITED(st)&&WEXITSTATUS(st)==0;ok&=check(owner,p,s2)==0;CK(hipSetDevice(owner));CK(hipFree(p));
 printf("IPC owner=%d accessing-device=%d %s\n",owner,acc,ok?"PASS":"FAIL");fflush(stdout);return ok;}
int main(int argc,char**argv){
 if(argc>=7&&!strcmp(argv[1],"--child"))return child(atoi(argv[2]),atoi(argv[3]),argv[4],(uint32_t)strtoul(argv[5],0,10),(uint32_t)strtoul(argv[6],0,10));
 int n=0;CK(hipGetDeviceCount(&n));if(n!=2){fprintf(stderr,"need exactly 2 devices, got %d\n",n);return 6;}
 for(int d=0;d<2;d++){char bus[32];CK(hipDeviceGetPCIBusId(bus,sizeof bus,d));for(char*c=bus;*c;c++)if(*c>=65&&*c<=90)*c+=32;printf("DEVICE %d %s\n",d,bus);}
 if(argc>=2&&!strcmp(argv[1],"local")){bool all=true;for(int d=0;d<2;d++){CK(hipSetDevice(d));uint32_t*p;CK(hipMalloc(&p,BYTES));bool ok=true;
  for(uint32_t k=0;k<3;k++){uint32_t s=0x2000u*(k+1)+d;fill<<<1024,256>>>(p,N,s);CK(hipGetLastError());CK(hipDeviceSynchronize());ok&=check(d,p,s)==0;}
  CK(hipSetDevice(d));CK(hipFree(p));printf("LOCAL device=%d patterns=3 %s\n",d,ok?"PASS":"FAIL");fflush(stdout);all&=ok;}return all?0:1;}
 int can01=0,can10=0;CK(hipDeviceCanAccessPeer(&can01,0,1));CK(hipDeviceCanAccessPeer(&can10,1,0));if(!can01||!can10){fprintf(stderr,"peer access unavailable\n");return 7;}
 peer(0,1);peer(1,0);bool d=direct(0,1);d&=direct(1,0);
 bool i=ipc(argv[0],0,1);i&=ipc(argv[0],1,0);
 printf("RESULT direct_integrity=%s ipc_integrity=%s directions=2\n",d?"true":"false",i?"true":"false");return d&&i?0:1;}
