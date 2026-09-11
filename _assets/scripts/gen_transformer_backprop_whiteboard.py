#!/usr/bin/env python3
"""Whiteboard-style computation-graph figures for the Transformer backprop note."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle
from matplotlib.font_manager import FontProperties

HAND = "/System/Library/Fonts/Supplemental/ChalkboardSE.ttc"
TITLE = "/System/Library/Fonts/Supplemental/Chalkduster.ttf"
fp = lambda s: FontProperties(fname=HAND, size=s)
fpt = lambda s: FontProperties(fname=TITLE, size=s)

INK = "#2B2B2B"; BLUE = "#2F5FA8"; RED = "#C0392B"; GREEN = "#2E7D5B"
F_BLUE = "#DCE9F7"; F_GREEN = "#DFF0E2"; F_YELLOW = "#FCF3D0"; F_PINK = "#FBE4E4"; F_GRAY = "#F1F1EC"
BG = "#FDFDFB"

plt.rcParams["path.sketch"] = (1, 90, 1.6)

def canvas(w, h, xlim, ylim):
    fig, ax = plt.subplots(figsize=(w, h))
    fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
    ax.set_xlim(*xlim); ax.set_ylim(*ylim); ax.axis("off")
    ax.add_patch(FancyBboxPatch((xlim[0]+1.5, ylim[0]+1.5), xlim[1]-xlim[0]-3, ylim[1]-ylim[0]-3,
                                boxstyle="round,pad=0.4,rounding_size=2", linewidth=1.4,
                                edgecolor="#D8D8D0", facecolor="none", linestyle=(0,(6,4))))
    return fig, ax

def box(ax, x, y, w, h, text, fc=F_GRAY, ec=INK, fs=12.5, lw=2.0, tc=INK):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.55,rounding_size=1.4",
                                linewidth=lw, edgecolor=ec, facecolor=fc))
    ax.text(x+w/2, y+h/2, text, ha="center", va="center",
            fontproperties=fp(fs), color=tc, linespacing=1.45)

def circle(ax, cx, cy, r, text, fc=F_YELLOW, ec=INK, fs=13):
    ax.add_patch(Circle((cx, cy), r, linewidth=2.0, edgecolor=ec, facecolor=fc))
    ax.text(cx, cy, text, ha="center", va="center", fontproperties=fp(fs), color=INK)

def arrow(ax, p1, p2, color=INK, dashed=False, lw=2.0, rad=0.0, ms=15):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=ms,
                                 linewidth=lw, color=color,
                                 linestyle=(0,(5,3)) if dashed else "solid",
                                 connectionstyle=f"arc3,rad={rad}", shrinkA=0, shrinkB=0))

def note(ax, x, y, text, color=RED, fs=11.5, ha="left", va="center"):
    ax.text(x, y, text, ha=ha, va=va, fontproperties=fp(fs), color=color, linespacing=1.5)

# ================================================================ figure 1
fig, ax = canvas(16, 7.8, (0, 152), (0, 74))
ax.text(4, 68, "Decoder-only Transformer: forward (solid) vs backward (dashed)",
        ha="left", va="center", fontproperties=fpt(17), color=INK)
ax.text(4, 60, "G_T = dL/dT  (same shape as T)      each step: downstream grad x local derivative, then add",
        ha="left", va="center", fontproperties=fp(12.0), color=BLUE)

labels = [
    "token ids\n[B,N]",
    "Embedding E\n+ pos -> H^(0)",
    "DecoderBlock x L\n(Pre-LN)",
    "Final LN",
    "LM head\nW_U : D x V",
    "logits Z\n[B,N,V]",
    "softmax + CE\nloss L",
]
xs = [4, 25, 46, 67, 88, 109, 130]
w, h, y = 17, 14, 34
fills = [F_GRAY, F_BLUE, F_GREEN, F_BLUE, F_YELLOW, F_BLUE, F_PINK]
for x, t, fc in zip(xs, labels, fills):
    box(ax, x, y, w, h, t, fc=fc)
for i in range(len(xs)-1):
    arrow(ax, (xs[i]+w+0.5, y+h/2), (xs[i+1]-0.5, y+h/2), color=INK, lw=2.0)

# backward arrows: one per gap, pointing left
by = 27
for i in range(len(xs)-1, 0, -1):
    arrow(ax, (xs[i]-0.5, by), (xs[i-1]+w+0.5, by), color=RED, dashed=True, lw=1.9, ms=13)

# labels assigned to gaps 5..0 (right to left)
gap_labels = {
    5: "G_Z = (1/N_eff) m * (P - P^tgt)",
    4: "G_Hf = G_Z W_U^T\nG_WU = Hf^T G_Z (sum b,t)",
    3: "Final LN backward:\nsubtract 2 averages",
    2: "per-block backprop\n(repeat x L)",
    1: "G_H^(0)",
    0: "G_E : scatter-add\nby token id",
}
order = [5, 4, 3, 2, 1, 0]
for j, gap in enumerate(order):
    cx = (xs[gap] + xs[gap+1] + w) / 2
    yy = 20 if j % 2 == 0 else 10.5
    ax.text(cx, yy, gap_labels[gap], ha="center", va="center",
            fontproperties=fp(11), color=RED, linespacing=1.45)

note(ax, 4, 2.5, "rules:  add -> gradients add   |   linear -> G_X = G_Y W^T   |   elementwise -> G_X = G_Y * phi'(X)   |   norm -> subtract the average",
     color=GREEN, fs=10.5)
fig.savefig("/tmp/wb/fig1.png", dpi=190, facecolor=BG, bbox_inches="tight")
plt.close(fig)

# ================================================================ figure 2
fig, ax = canvas(16, 12.2, (0, 164), (-26, 110))
ax.text(6, 104, "One DecoderBlock: Pre-LN block (left) + attention internals (right)",
        ha="left", va="center", fontproperties=fpt(15), color=INK)
ax.text(6, 97.5, "black = forward      red = backward gradient", ha="left", va="center",
        fontproperties=fp(12), color=BLUE)

# ---------------- left pipeline: Pre-LN block
lx, lw_, lh = 8, 30, 9.0
nodes = [
    (84, "X   [B,N,D]", F_GRAY),
    (70, "LN1", F_BLUE),
    (56, "causal MHA", F_GREEN),
    (42, "+", F_YELLOW),
    (28, "LN2", F_BLUE),
    (14, "MLP", F_GREEN),
    (0,  "+", F_YELLOW),
]
for yy, t, fc in nodes:
    if t == "+":
        circle(ax, lx + lw_/2, yy + lh/2, 4.0, "+", fc=fc)
    else:
        box(ax, lx, yy, lw_, lh, t, fc=fc, fs=12)
for i in range(len(nodes)-1):
    arrow(ax, (lx + lw_/2, nodes[i][0]), (lx + lw_/2, nodes[i+1][0] + lh + 0.6), color=INK, lw=2.0, ms=13)
arrow(ax, (lx + lw_/2, 0), (lx + lw_/2, -10.0), color=INK, lw=2.0, ms=13)
box(ax, lx, -19.0, lw_, lh, "Y   [B,N,D]", fc=F_GRAY, fs=12)

# residual arcs on the right of the block column
arrow(ax, (lx + lw_, 88.5), (lx + lw_/2 + 5.0, 46.5), color=INK, lw=1.8, rad=-0.42, ms=13)
arrow(ax, (lx + lw_/2 + 5.0, 42), (lx + lw_/2 + 5.0, 4.5), color=INK, lw=1.8, rad=-0.42, ms=13)

# backward annotations next to the block
bx = lx + lw_ + 20
note(ax, bx, 88, "G_X", color=RED, fs=11)
note(ax, bx, 74, "LN1 backward -> G_X (2nd path)", color=RED, fs=11)
note(ax, bx, 60, "G_L1 = G_Q W_Q^T\n+ G_K W_K^T + G_V W_V^T", color=RED, fs=10.5)
note(ax, bx, 46, "G_X = G_U + LNback(G_L1)", color=RED, fs=11)
note(ax, bx, 32, "LN2 backward -> G_U (2nd path)", color=RED, fs=11)
note(ax, bx, 18, "G_F2 = G_MLP W_2^T\nG_F1 = G_F2 * phi'(F1)\nG_L2 = G_F1 W_1^T", color=RED, fs=10.5)
note(ax, bx, -4, "G_U = G_Y + LNback(G_L2)", color=RED, fs=11)

# ---------------- right pipeline: attention internals
rx, rw, rh = 104, 36, 9.0
att = [
    (84, "L1 = LN1(X)   [N,D]", F_BLUE),
    (70, "Q,K,V = L1 W_Q , L1 W_K , L1 W_V", F_GRAY),
    (56, "S = Q K^T / sqrt(d_h)", F_GREEN),
    (42, "+ causal mask M", F_YELLOW),
    (28, "A = softmax_row(S + M)", F_GREEN),
    (14, "C = A V", F_GREEN),
    (0,  "concat heads -> W_O -> out", F_GRAY),
]
for yy, t, fc in att:
    box(ax, rx, yy, rw, rh, t, fc=fc, fs=10.5)
for i in range(len(att)-1):
    arrow(ax, (rx + rw/2, att[i][0]), (rx + rw/2, att[i+1][0] + rh + 0.6), color=INK, lw=2.0, ms=13)

nx = rx + rw + 4
note(ax, nx, 88, "G_L1 = G_Q W_Q^T\n+ G_K W_K^T + G_V W_V^T", color=RED, fs=10)
note(ax, nx, 74, "G_Q = G_S K / sqrt(d_h)\nG_K = G_S^T Q / sqrt(d_h)\nG_V = A^T G_C", color=RED, fs=10)
note(ax, nx, 58, "G_S = G_(S+M) * 1[M=0]", color=RED, fs=10)
note(ax, nx, 44, "G_(S+M) = A * (G_A\n- rowsum(G_A * A) 1^T)", color=RED, fs=10)
note(ax, nx, 30, "G_A = G_C V^T", color=RED, fs=10)
note(ax, nx, 16, "G_C = G_out W_O^T", color=RED, fs=10)

fig.savefig("/tmp/wb/fig2.png", dpi=190, facecolor=BG, bbox_inches="tight")
plt.close(fig)
print("done")
