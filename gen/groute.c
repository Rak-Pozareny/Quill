/* Grid router core for gen/groute.py (compiled at run time: gcc -O2 -shared -fPIC).
 *
 * The board is a grid of square cells (res mm) on each routing layer. Three kinds of rasters:
 *   st_t[l]  static owner of a track cell: 0 free, net id, -1 blocked (two nets, keepout, outside the board).
 *            Static copper is inflated so that a default-width track centred in a free cell keeps its clearance.
 *   st_v     static owner of a via cell (all layers at once: a via goes through the board).
 *   dy_t[l], dy_v   how many routed nets (other than the one being routed) cover the cell: rip-up / re-route.
 *   hist[l], hist_v history cost of the negotiated-congestion loop (PathFinder).
 * A route is a path of cells (layer, i, j); moves are the 8 grid directions with turns of at most 90 degrees
 * (45-degree turns cheap, 90-degree turns dear) and vias (same cell, another layer).
 */
#include <math.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

/* ------------------------------------------------------------------------------------------------ rasterising */

/* scan-line fill of a polygon (mm, closed implicitly) with owner semantics: free -> val, same -> val, else -1 */
void fill_poly(int32_t *a, int nx, int ny, double x0, double y0, double res, const double *pts, int n, int32_t val)
{
    double ymin = 1e18, ymax = -1e18;
    for (int k = 0; k < n; k++) {
        if (pts[2 * k + 1] < ymin) ymin = pts[2 * k + 1];
        if (pts[2 * k + 1] > ymax) ymax = pts[2 * k + 1];
    }
    int j0 = (int)floor((ymin - y0) / res), j1 = (int)ceil((ymax - y0) / res);
    if (j0 < 0) j0 = 0;
    if (j1 > ny - 1) j1 = ny - 1;
    double *xs = malloc(sizeof(double) * (n + 2));
    for (int j = j0; j <= j1; j++) {
        double y = y0 + (j + 0.5) * res;
        int m = 0;
        for (int k = 0; k < n; k++) {
            double ax = pts[2 * k], ay = pts[2 * k + 1];
            double bx = pts[2 * ((k + 1) % n)], by = pts[2 * ((k + 1) % n) + 1];
            if ((ay > y) != (by > y)) xs[m++] = ax + (y - ay) * (bx - ax) / (by - ay);
        }
        for (int p = 1; p < m; p++) {               /* insertion sort, m is small */
            double v = xs[p];
            int q = p - 1;
            while (q >= 0 && xs[q] > v) { xs[q + 1] = xs[q]; q--; }
            xs[q + 1] = v;
        }
        for (int p = 0; p + 1 < m; p += 2) {
            int i0 = (int)ceil((xs[p] - x0) / res - 0.5), i1 = (int)floor((xs[p + 1] - x0) / res - 0.5);
            if (i0 < 0) i0 = 0;
            if (i1 > nx - 1) i1 = nx - 1;
            int32_t *row = a + (size_t)j * nx;
            for (int i = i0; i <= i1; i++) {
                int32_t c = row[i];
                if (c == 0 || c == val) row[i] = val;
                else if (val == -1 || c != -1) row[i] = -1;
            }
        }
    }
    free(xs);
}

/* add delta to every cell whose centre lies within r of segment a-b (a capsule) */
void mark_capsule(uint16_t *a, int nx, int ny, double x0, double y0, double res,
                  double ax, double ay, double bx, double by, double r, int delta)
{
    double lx = fmin(ax, bx) - r, hx = fmax(ax, bx) + r, ly = fmin(ay, by) - r, hy = fmax(ay, by) + r;
    int i0 = (int)floor((lx - x0) / res), i1 = (int)ceil((hx - x0) / res);
    int j0 = (int)floor((ly - y0) / res), j1 = (int)ceil((hy - y0) / res);
    if (i0 < 0) i0 = 0;
    if (j0 < 0) j0 = 0;
    if (i1 > nx - 1) i1 = nx - 1;
    if (j1 > ny - 1) j1 = ny - 1;
    double dx = bx - ax, dy = by - ay, L2 = dx * dx + dy * dy;
    for (int j = j0; j <= j1; j++) {
        double y = y0 + (j + 0.5) * res;
        for (int i = i0; i <= i1; i++) {
            double x = x0 + (i + 0.5) * res;
            double t = L2 > 0 ? ((x - ax) * dx + (y - ay) * dy) / L2 : 0;
            if (t < 0) t = 0;
            if (t > 1) t = 1;
            double ex = x - ax - t * dx, ey = y - ay - t * dy;
            if (ex * ex + ey * ey <= r * r) {
                uint16_t *c = a + (size_t)j * nx + i;
                int v = (int)*c + delta;
                *c = (uint16_t)(v < 0 ? 0 : v);
            }
        }
    }
}

/* -------------------------------------------------------------------------------------------------- A* search */

typedef struct { float f; int32_t s; } HItem;
typedef struct { HItem *h; int n, cap; } Heap;

static void hpush(Heap *q, float f, int32_t s)
{
    if (q->n == q->cap) { q->cap = q->cap ? q->cap * 2 : 1024; q->h = realloc(q->h, sizeof(HItem) * q->cap); }
    int i = q->n++;
    while (i > 0) {
        int p = (i - 1) / 2;
        if (q->h[p].f <= f) break;
        q->h[i] = q->h[p];
        i = p;
    }
    q->h[i].f = f;
    q->h[i].s = s;
}

static HItem hpop(Heap *q)
{
    HItem top = q->h[0], last = q->h[--q->n];
    int i = 0;
    for (;;) {
        int c = 2 * i + 1;
        if (c >= q->n) break;
        if (c + 1 < q->n && q->h[c + 1].f < q->h[c].f) c++;
        if (q->h[c].f >= last.f) break;
        q->h[i] = q->h[c];
        i = c;
    }
    q->h[i] = last;
    return top;
}

static const int DI[8] = {1, 1, 0, -1, -1, -1, 0, 1};
static const int DJ[8] = {0, 1, 1, 1, 0, -1, -1, -1};

/*
 * Route net `net` inside window [wi0, wi0+ww) x [wj0, wj0+wh) of the full grid (nx x ny), on layers with
 * lcost[l] > 0. Cells: free when the static owner is 0 or net (and, with an extra radius, every cell of the extra
 * disk too: extra_t for tracks, extra_n within `neck` cells of an end, extra_v for vias). Congestion cost per step: len * lcost * (1 + hist) * (1 + pres * dy).
 * starts / goals: triplets (l, i, j) in full-grid coordinates. goal_any: a goal cell may be reached on any layer.
 * out: path as triplets (l, i, j), start first; returns its length in cells, 0 if none, -1 if out is too small,
 * -2 when the expansion budget ran out.
 */
int astar(int nx, int ny, int nl, int32_t **st_t, int32_t *st_v, uint16_t **dy_t, uint16_t *dy_v,
          float **hist, float *hist_v, int32_t net,
          int wi0, int wj0, int ww, int wh, const double *lcost,
          const int32_t *starts, int ns, const int32_t *goals, int ng,
          const int32_t *extra_t, int n_extra_t, const int32_t *extra_v, int n_extra_v,
          const int32_t *extra_n, int n_extra_n,
          double via_cost, double t45, double t90, double pres, int allow_via, long max_expand,
          int neck, long full_max, int32_t *out, int out_cap)
{
    /* Labels per (cell, arrival direction) when the window has at most full_max of them (exact turn costs);
       otherwise one label per cell, the arrival direction kept with the label and the turn cost charged from it
       (8 x less state and time, slightly less exact) */
    long ncell = (long)nl * ww * wh;
    int full = ncell * 8 <= full_max;
    long nstate = full ? ncell * 8 : ncell;
#define ST(cell, dir) (full ? (((long)(cell)) << 3 | (dir)) : (long)(cell))
    float *g = malloc(sizeof(float) * nstate);
    int32_t *par = malloc(sizeof(int32_t) * nstate);
    int8_t *din = full ? NULL : malloc(nstate);
    uint8_t *closed = calloc(nstate, 1);
    uint8_t *goalm = calloc((size_t)nl * ww * wh, 1);
    uint8_t *okc = malloc((size_t)nl * ww * wh);       /* cached cell test: 0 unknown, 1 free, 2 blocked */
    uint8_t *okv = calloc((size_t)ww * wh, 1);
    uint16_t *occ = malloc(sizeof(uint16_t) * (size_t)nl * ww * wh);   /* occupancy over the extra disk */
    memset(occ, 0xff, sizeof(uint16_t) * (size_t)nl * ww * wh);
    memset(okc, 0, (size_t)nl * ww * wh);
    for (long k = 0; k < nstate; k++) g[k] = 1e30f;
    int gi0 = 1 << 30, gi1 = -(1 << 30), gj0 = 1 << 30, gj1 = -(1 << 30);
    for (int k = 0; k < ng; k++) {
        int l = goals[3 * k], i = goals[3 * k + 1] - wi0, j = goals[3 * k + 2] - wj0;
        if (i < 0 || j < 0 || i >= ww || j >= wh) continue;
        if (l < 0) { for (int m = 0; m < nl; m++) goalm[((size_t)m * wh + j) * ww + i] = 1; }
        else goalm[((size_t)l * wh + j) * ww + i] = 1;
        if (i < gi0) gi0 = i;
        if (i > gi1) gi1 = i;
        if (j < gj0) gj0 = j;
        if (j > gj1) gj1 = j;
    }
    Heap q = {0};
    const float SQ2 = 1.41421356f;
#define CELL_OK(l, i, j) cell_ok(l, i, j)
    /* within `neck` cells of an end the route may run at the default width (fine-pitch pins): no extra disk */
    int near_end(int i, int j) {
        if (neck <= 0) return 0;
        for (int k = 0; k < ns; k++) {
            int di = i + wi0 - starts[3 * k + 1], dj = j + wj0 - starts[3 * k + 2];
            if (di * di + dj * dj <= neck * neck) return 1;
        }
        for (int k = 0; k < ng; k++) {
            int di = i + wi0 - goals[3 * k + 1], dj = j + wj0 - goals[3 * k + 2];
            if (di * di + dj * dj <= neck * neck) return 1;
        }
        return 0;
    }
    int cell_ok(int l, int i, int j) {
        size_t w = ((size_t)l * wh + j) * ww + i;
        if (okc[w]) return okc[w] == 1;
        int gi = i + wi0, gj = j + wj0, ok = 1;
        int32_t o = st_t[l][(size_t)gj * nx + gi];
        if (o != 0 && o != net) ok = 0;
        /* near an end: the default width, with the net's own clearance (the neck disk extra_n) */
        int ne = near_end(i, j);
        const int32_t *ex = ne ? extra_n : extra_t;
        int nex = ne ? n_extra_n : n_extra_t;
        for (int k = 0; ok && k < nex; k++) {
            int ii = gi + ex[2 * k], jj = gj + ex[2 * k + 1];
            if (ii < 0 || jj < 0 || ii >= nx || jj >= ny) { ok = 0; break; }
            int32_t oo = st_t[l][(size_t)jj * nx + ii];
            if (oo != 0 && oo != net) ok = 0;
        }
        okc[w] = ok ? 1 : 2;
        return ok;
    }
    uint16_t occupancy(int l, int i, int j) {
        size_t w = ((size_t)l * wh + j) * ww + i;
        if (occ[w] != 0xffff) return occ[w];
        int gi = i + wi0, gj = j + wj0;
        uint16_t m = dy_t[l][(size_t)gj * nx + gi];
        int ne = near_end(i, j);
        const int32_t *ex = ne ? extra_n : extra_t;
        int nex = ne ? n_extra_n : n_extra_t;
        for (int k = 0; k < nex; k++) {
                int ii = gi + ex[2 * k], jj = gj + ex[2 * k + 1];
                if (ii < 0 || jj < 0 || ii >= nx || jj >= ny) continue;
                uint16_t v = dy_t[l][(size_t)jj * nx + ii];
                if (v > m) m = v;
            }
        occ[w] = m;
        return m;
    }
    int via_ok(int i, int j) {
        size_t w = (size_t)j * ww + i;
        if (okv[w]) return okv[w] == 1;
        int gi = i + wi0, gj = j + wj0, ok = 1;
        int32_t o = st_v[(size_t)gj * nx + gi];
        if (o != 0 && o != net) ok = 0;
        for (int k = 0; ok && k < n_extra_v; k++) {
            int ii = gi + extra_v[2 * k], jj = gj + extra_v[2 * k + 1];
            if (ii < 0 || jj < 0 || ii >= nx || jj >= ny) { ok = 0; break; }
            int32_t oo = st_v[(size_t)jj * nx + ii];
            if (oo != 0 && oo != net) ok = 0;
        }
        okv[w] = ok ? 1 : 2;
        return ok;
    }
    double lmin = 1e9;
    for (int l = 0; l < nl; l++) if (lcost[l] > 0 && lcost[l] < lmin) lmin = lcost[l];
    float hfun(int i, int j) {
        int di = i < gi0 ? gi0 - i : (i > gi1 ? i - gi1 : 0);
        int dj = j < gj0 ? gj0 - j : (j > gj1 ? j - gj1 : 0);
        int mn = di < dj ? di : dj, mx = di < dj ? dj : di;
        return (float)((mx - mn + SQ2 * mn) * lmin);
    }
    for (int k = 0; k < ns; k++) {
        int l = starts[3 * k], i = starts[3 * k + 1] - wi0, j = starts[3 * k + 2] - wj0;
        if (i < 0 || j < 0 || i >= ww || j >= wh) continue;
        for (int m = 0; m < nl; m++) {
            if (l >= 0 && m != l) continue;
            if (lcost[m] <= 0) continue;
            long cell = ((long)m * wh + j) * ww + i;
            for (int d = 0; d < (full ? 8 : 1); d++) {
                long s = ST(cell, d);
                g[s] = 0;
                par[s] = -1;
                if (!full) din[s] = -1;
                hpush(&q, hfun(i, j), (int32_t)s);
            }
        }
    }
    long expanded = 0;
    int32_t found = -1;
    while (q.n) {
        HItem it = hpop(&q);
        long s = it.s;
        if (closed[s]) continue;
        closed[s] = 1;
        int d = full ? (int)(s & 7) : din[s];
        long c = full ? s >> 3 : s;
        int i = c % ww, j = (c / ww) % wh, l = c / ((long)ww * wh);
        if (goalm[c]) { found = (int32_t)s; break; }
        if (++expanded > max_expand) break;
        float gs = g[s];
        size_t gc = (size_t)(j + wj0) * nx + (i + wi0);
        for (int dd = (d < 0 ? -4 : -2); dd <= (d < 0 ? 3 : 2); dd++) {   /* straight, 45 / 90 degree turns */
            int nd = ((d < 0 ? 0 : d) + dd + 8) & 7;
            int ni = i + DI[nd], nj = j + DJ[nd];
            if (ni < 0 || nj < 0 || ni >= ww || nj >= wh) continue;
            if (!cell_ok(l, ni, nj)) continue;
            size_t ngc = (size_t)(nj + wj0) * nx + (ni + wi0);
            float len = (nd & 1) ? SQ2 : 1.0f;
            float cost = len * (float)lcost[l] * (1.0f + hist[l][ngc]) * (1.0f + (float)pres * occupancy(l, ni, nj));
            if (d >= 0) cost += (dd == 0) ? 0.0f : ((dd == 1 || dd == -1) ? (float)t45 : (float)t90);
            long ns2 = ST(((long)l * wh + nj) * ww + ni, nd);
            if (closed[ns2]) continue;
            float ng2 = gs + cost;
            if (ng2 < g[ns2]) {
                g[ns2] = ng2;
                par[ns2] = (int32_t)s;
                if (!full) din[ns2] = (int8_t)nd;
                hpush(&q, ng2 + hfun(ni, nj), (int32_t)ns2);
            }
        }
        if (allow_via && via_ok(i, j)) {
            float vc = (float)via_cost * (1.0f + hist_v[gc]) * (1.0f + (float)pres * dy_v[gc]);
            for (int m = 0; m < nl; m++) {
                if (m == l || lcost[m] <= 0 || !cell_ok(m, i, j)) continue;
                long ns2 = ST(((long)m * wh + j) * ww + i, d < 0 ? 0 : d);
                if (closed[ns2]) continue;
                float ng2 = gs + vc;
                if (ng2 < g[ns2]) {
                    g[ns2] = ng2;
                    par[ns2] = (int32_t)s;
                    if (!full) din[ns2] = (int8_t)d;
                    hpush(&q, ng2 + hfun(i, j), (int32_t)ns2);
                }
            }
        }
    }
    int n = 0;
    if (found >= 0) {
        long s = found;
        while (s >= 0) {
            if (n >= out_cap) { n = -1; break; }
            long c = full ? s >> 3 : s;
            int i = c % ww, j = (c / ww) % wh, l = c / ((long)ww * wh);
            out[3 * n] = l;
            out[3 * n + 1] = i + wi0;
            out[3 * n + 2] = j + wj0;
            n++;
            s = par[s];
        }
        if (n > 0) {                                     /* reverse: start first */
            for (int a = 0, b = n - 1; a < b; a++, b--)
                for (int k = 0; k < 3; k++) { int32_t t = out[3 * a + k]; out[3 * a + k] = out[3 * b + k]; out[3 * b + k] = t; }
        }
    } else if (expanded > max_expand) n = -2;
    free(g); free(par); if (din) free(din); free(closed); free(goalm); free(okc); free(okv); free(occ); free(q.h);
    return n;
}
