# ORAM Simulator

A small Python simulator for studying **Oblivious RAM (ORAM)** access-pattern hiding.

This project is meant as a learning and experimentation tool. It starts with deliberately insecure storage, then builds up the main pieces of Path ORAM:

- server-visible access traces,
- access-pattern workloads,
- leakage analysis,
- a binary tree server,
- a private position map,
- a private stash,
- a minimal Path ORAM read/write implementation.

The goal is to make the privacy idea visible: in naive storage, repeated logical accesses directly reveal repeated physical accesses; in Path ORAM, logical blocks are remapped to fresh random leaves, making the server-visible path sequence much less directly tied to the logical workload.

## Current status

Implemented:

- `NaiveStorage`
- `AccessTrace`
- workload generators:
  - sequential access
  - repeated access
  - random access
  - hotspot/locality-heavy access
- leakage summaries
- adjacent-repeat leakage comparison
- binary tree server with fixed-capacity buckets
- ORAM block model
- private position map
- private stash
- minimal `PathORAM.read`
- minimal `PathORAM.write`
- comparison demos between naive storage and Path ORAM

Not yet implemented:

- encryption
- dummy blocks
- fixed-size encrypted buckets at the API boundary
- recursive position map
- stash overflow probability experiments
- formal security experiments
- performance benchmarking

So this is currently a **pedagogical simulator**, not a production ORAM library.

## Project layout

```text
oram-simulator/
  src/
    oram_sim/
      access_patterns.py
      analysis.py
      block.py
      experiments.py
      path_oram.py
      position_map.py
      stash.py
      storage.py
      trace.py
      tree.py
  scripts/
    demo_compare_naive_path_oram.py
    demo_naive_leakage.py
    demo_path_oram_access.py
    demo_path_oram_initialization.py
    demo_position_map.py
    demo_stash.py
    demo_tree_server.py
  tests/
    test_access_patterns.py
    test_analysis.py
    test_block.py
    test_experiments.py
    test_path_oram.py
    test_position_map.py
    test_stash.py
    test_storage.py
    test_tree.py
    