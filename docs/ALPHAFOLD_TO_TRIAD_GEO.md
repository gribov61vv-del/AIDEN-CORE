# From AlphaFold to TRIAD-GEO: what transfers, what does not

Date: 2026-11-09
Status: research note + small educational prototype

## Executive conclusion

AlphaFold2 is not a generic three-box energy-transfer system. It is a trained neural architecture for protein-structure prediction. Its central transferable computational idea for TRIAD is to represent a complex object through both local features and pairwise relations, let those representations exchange information, and iteratively refine a candidate geometry while checking geometric consistency.

TRIAD-GEO implements only a narrow, transparent slice of that idea: weighted pairwise-distance constraints on a graph, triangle-inequality auditing, and iterative coordinate fitting. It is a mathematical experiment, not a biological predictor and not a reproduction of AlphaFold.

## What AlphaFold2 actually does

The 2021 AlphaFold2 paper describes a network that takes an amino-acid sequence and aligned homologous sequences (an MSA), with optional templates, and predicts atomic coordinates. Its trunk jointly processes:
- an MSA representation: rows are aligned sequences and columns correspond to sequence positions;
- a pair representation: features for residue pairs.

The Evoformer repeatedly exchanges information between these representations. Pair updates include triangle-based operations: two relations through an intermediate residue help update the relation between the other two residues. The paper interprets this as graph inference in 3D, where edges represent residue relationships. A structure module then builds/refines 3D backbone frames using invariant point attention. Recycling feeds a previous prediction back through the network for further refinement.

The full system depends on learned parameters, training data, evolutionary information, geometric representations, and specialized losses. Replacing these with a few hand-written equations does not recreate AlphaFold.

## Transfer map for TRIAD

| AlphaFold2 concept | Abstract computational pattern | TRIAD-GEO analogue | Not implemented |
|---|---|---|---|
| MSA representation | evidence/features attached to nodes | named graph nodes and optional future node metadata | sequence alignments, evolutionary embeddings |
| Pair representation | relations attached to node pairs | weighted target distances | learned pair embeddings |
| Triangle updates | use two edges to refine a third relation | triangle-inequality audit | Evoformer attention/multiplicative updates |
| Structure module | convert relational state into 3D coordinates | coordinate fitting by gradient descent | invariant point attention, residue frames, atom geometry |
| Recycling | repeatedly refine a candidate | iterative reduction of distance stress | learned recycling trunk and trained losses |
| pLDDT / PAE | confidence estimates for local structure / relative placement | edge residuals and constraint consistency only | calibrated predictive confidence; residuals are not pLDDT or PAE |

## Mathematical core

Let the graph be G=(V,E). Each observed edge (i,j) carries a target distance d_ij>0 and weight w_ij>0. We seek coordinates x_i in R^D, where D is 2 or 3, that minimize weighted stress:

    L(X) = [1 / sum(w_ij)] * sum over edges (i,j) of w_ij * (||x_i-x_j||_2 - d_ij)^2

For one edge, the coordinate gradient contribution is

    grad_xi L_ij = 2*w_ij/sum(w) * (||x_i-x_j|| - d_ij) * (x_i-x_j)/||x_i-x_j||

and the contribution for x_j is its negative. The implementation uses deterministic initialization, gradient descent, and centering to remove translational drift.

For any three nodes with all three distances known, a necessary Euclidean condition is the triangle inequality:

    d_ij <= d_ik + d_kj

A violation is sufficient to reject that set of exact distances. Passing this check is not sufficient to prove that a whole distance graph is realizable in 2D/3D, nor that the fitted geometry is unique.

## What the prototype returns

triad_engine/structure_inference.py provides:
- input validation and connected-graph check;
- optional positive weights on distance constraints;
- triangle-inequality checks for fully observed triples;
- deterministic 2D/3D coordinate fitting;
- weighted mean-squared distance error and per-edge residuals;
- explicit warnings about non-uniqueness and scientific scope.

Run:

    cd ~/AIDEN-CORE/triad_engine
    python test_structure_inference.py

No external packages, model downloads, network calls, or modifications to the live TRIAD SQLite memory are required.

## Scientific boundaries and next experiments

1. Add a separate node-feature table and typed pair relations; do not mix them with the live append-only evidence ledger until the schema is reviewed.
2. Add a stress-test suite for noisy and incomplete graphs, with reproducible synthetic ground-truth geometries.
3. Compare gradient descent with classical multidimensional scaling / SMACOF on the same benchmark set.
4. Add uncertainty intervals only when there is a defensible statistical model; do not relabel residuals as confidence.
5. If protein biology is ever a real target, use validated protein-specific tools and experimental reference structures. TRIAD-GEO alone is not suitable for biomedical decisions.

## Sources

- Jumper et al., “Highly accurate protein structure prediction with AlphaFold,” Nature 596, 583–589 (2021), https://doi.org/10.1038/s41586-021-03819-2
- AlphaFold Protein Structure Database, EMBL-EBI, https://alphafold.ebi.ac.uk/
- AlphaFold DB FAQ, confidence metrics and limitations, https://alphafold.ebi.ac.uk/faq

## Project decision

Keep the three-pass TRIAD discipline:
1. evidence and provenance;
2. explicit calculation;
3. independent consistency checks and caveats.

Keep this geometry prototype separate from Model A (“digital continent”), Model B (invariant-mass hypothesis), and the unverified triple-energy-node hypothesis. No physical connection is implied by the shared use of graphs or iterative refinement.


## TRIAD-GEO method comparison extension

A second research layer now compares three distinct numerical approaches:
- weighted gradient descent (the original transparent prototype);
- weighted SMACOF majorization for connected sparse graphs;
- classical metric MDS for complete distance matrices.

The methods, tests, and reproducible synthetic benchmark live in `triad_engine/geometry_methods.py`, `triad_engine/test_geometry_methods.py`, and `triad_engine/benchmark_geometry.py`. See `triad_engine/GEOMETRY_METHODS.md` for benchmark results and interpretation.

Important refinement: exact triangle-inequality rejection remains the default. When observations are known to contain measurement noise, the original fitter can be explicitly run with `reject_triangle_violations=False`; violations are then reported, not silently discarded. This is a least-squares experiment, not a claim that inconsistent distances are physically exact.
