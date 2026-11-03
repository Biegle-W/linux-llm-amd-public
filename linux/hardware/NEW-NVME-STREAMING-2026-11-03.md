# New NVMe streaming-model placement — November 3, 2026

The owner requested that new SSD-streaming models use the new NVMe. The detected additional Crucial P3 Plus 1 TB drive is mounted and had approximately 932 GiB free before placement. No performance qualification is implied by its capacity or model name.

The new streaming placement helper verifies that exact volume before creating a model directory, rejects a wrong or absent disk, enforces the existing below-90%-used ceiling, and never falls back to another disk. Admission accepts future model paths on this volume. Static checkpoints retain their established SATA placement; existing streaming profiles keep their current backing until a separately verified migration.

The newly prepared DFlash2 source and both runtime packs now reside on the new NVMe. Each copied artifact was fully SHA-256 checked before its staging entry was replaced by a link. The drafter remains isolated and unqualified. Both maintained checkouts pass 26 focused storage checks, including wrong-volume rejection before directory creation, capacity refusal and new-volume path admission. Public paths and disk identity are configurable examples.

The owner clarified that GPU-led model inference with some CPU expert offload is permitted; running an entire model on the CPU is excluded. The RCCL CPU build compiles a GPU communication library and performs no model inference. Its owned scope continues, frozen only during guarded timing and thawed afterward.

The first isolated Strata Off trial was stopped for that clarification, with no new GPU fault. Its owned scopes emptied and KFD clients cleared. Three completed code trials are retained; the continuation measures the remaining prose/retrieval/tool checks in a new process and records the interruption, rather than repeating those code samples. No completed comparison or promotion is claimed. Maya GLM remains disabled, and the recurring updater remains paused.
