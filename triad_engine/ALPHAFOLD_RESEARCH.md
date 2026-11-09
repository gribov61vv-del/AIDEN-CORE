# AlphaFold research handoff

The research note and prototype are documented in docs/ALPHAFOLD_TO_TRIAD_GEO.md.

Prototype: structure_inference.py
Tests: test_structure_inference.py

This module is deliberately isolated from the live TRIAD API and SQLite memory. It is a generic distance-geometry experiment, not a protein predictor or AlphaFold implementation.
