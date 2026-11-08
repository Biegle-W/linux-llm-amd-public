# Agent entry point

This is the sanitized public reference for a dual RX 7900 XTX Linux server. The private operational repository is maintained separately; configure example paths locally. Read in order and stop when you have what you need:

1. [README.md](README.md): scope, rules and the doc map.
2. [Runtime handoff](linux/network/LINUX-LLM-RUNTIME-HANDOFF.md): current state, enabled routes, guards, pins and open items.
3. [Current results](linux/hardware/CURRENT-AMD-BENCHMARKS.md): only when the task needs measurements.
4. [Changelog](linux/hardware/CHANGELOG.md): what changed recently, with links to the dated reports.

Before acting on a real machine, check the Git tree, the GPU lock (`hardware/generated/GPU-LOCK`; absent means no hold) and the actual inference processes and `/dev/kfd` users. Never stop work you did not start.

After authorized work, replace current state in the handoff and results index. Do not prepend dated paragraphs: add one line to the [changelog](linux/hardware/CHANGELOG.md) and put the evidence in a dated report. Keep private workflow and client state out of public exports.

Older entry docs: [November 5 snapshot](linux/hardware/history/documentation-2026-11-05/README.md) and Git history. They are not startup reading.
