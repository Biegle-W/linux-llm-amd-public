// Negative HIP capability/enable check. No kernels or remote-memory accesses.
#include <hip/hip_runtime_api.h>
#include <fstream>
#include <iostream>
#include <string>

static bool check(hipError_t e) {
    if (e == hipSuccess) return true;
    std::cerr << hipGetErrorName(e) << ": " << hipGetErrorString(e) << '\n';
    return false;
}
int main() {
    std::string pcie, xgmi;
    std::ifstream("/sys/module/amdgpu/parameters/pcie_p2p") >> pcie;
    std::ifstream("/sys/module/amdgpu/parameters/use_xgmi_p2p") >> xgmi;
    if (pcie != "N" || xgmi != "0") {
        std::cerr << "Refusing HIP initialization: driver P2P disable is not active\n";
        return 2;
    }
    int count = 0;
    if (!check(hipGetDeviceCount(&count)) || count != 2) return 3;
    bool passed = true;
    for (int d = 0; d < count; ++d) {
        char bus[32] = {}, peer_bus[32] = {};
        if (!check(hipSetDevice(d)) || !check(hipDeviceGetPCIBusId(bus, sizeof(bus), d))) return 4;
        // Establish that both indices name real, distinct devices before interpreting
        // ROCm 7.2.3's hipErrorInvalidDevice as its unsupported-peer error.
        if (!check(hipDeviceGetPCIBusId(peer_bus, sizeof(peer_bus), 1-d)) ||
            std::string(bus) == std::string(peer_bus)) return 4;
        std::cout << "device=" << d << " pci=" << bus << '\n';
        int can = -1;
        if (!check(hipDeviceCanAccessPeer(&can, d, 1-d))) return 5;
        auto enabled = hipDeviceEnablePeerAccess(1-d, 0);
        std::cout << d << "->" << 1-d << " can_access=" << can
                  << " enable=" << hipGetErrorName(enabled) << '\n';
        if (enabled == hipSuccess) {
            check(hipDeviceDisablePeerAccess(1-d));
            passed = false;
        }
        // CLR rocm-7.2.3 hip_peer.cpp returns hipErrorInvalidDevice when its
        // valid-device canAccessPeer query returns zero. Do not accept other errors.
        bool refused = enabled == hipErrorPeerAccessUnsupported || enabled == hipErrorInvalidDevice;
        if (can != 0 || !refused) passed = false;
        (void)hipGetLastError();
    }
    std::cout << (passed ? "PASS: both peer capabilities absent and enable requests refused\n"
                         : "FAIL: peer disable not established\n");
    return passed ? 0 : 6;
}
