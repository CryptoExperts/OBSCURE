"""
See example() for usage and
canonical_run() for reference permutation evaluation code.
"""
from typing import Tuple, List
from random import shuffle, randrange
from collections import defaultdict


def example():
    m = 5  # shuffle 2**5 = 32 elements
    le = 3  # each MI has 2**3 = 8 inputs/outputs

    f = [randrange(2**m) for _ in range(2**m)]
    # BDBFuncMI : Benes-Duplicates-Benes method
    # for implementing function with MultiInstructions.
    # Computes a "program" which is a sequence of layers,
    # PublicShuffle - public wiring
    # SecretShuffles - secret permutations at given offsets (may be not over full state at once)
    bf = BDBFuncMI(f, le=le)

    program = optimize(bf.canonical())
    ff = canononical_run(program, m)

    assert tuple(f) == tuple(bf.apply())

    print("result:", ff)
    print("target:", f)
    assert ff == f
    print()


def canononical_run(program, m):
    """Verbose execution of a canonical representation."""
    # generate input list to be permuted
    ff = list(range(2**m))

    for row in program:
        if isinstance(row, PublicShuffle):
            # PublicShuffle is a wrapped permutation (tuple)
            print("public permutation (wiring):", row)
            ff = [ff[i] for i in row]

        elif isinstance(row, SecretShuffles):
            # SecretShuffles is wrapped dict
            # {offset : SecretShuffle}
            #     each SecretShuffle is a wrapped permutation (tuple)
            print("secret permutations:")
            for off, perm in row.items():
                print("   ", f"offset {off:03d} MI permutation:", perm)
                assert len(perm) == perm.input_size, "only fixed-size permutations supported"
                n = len(perm)
                ff[off:off+n] = [ff[off+i] for i in perm]
        else:
            raise RuntimeError()
    print()
    return ff


def optimize(program):
    optimized = True
    while optimized:
        optimized = False

        # remove identity maps
        ret = []
        for row in program:
            if isinstance(row, PublicShuffle) and list(row) == list(range(len(row))):
                #print("[O] removed public identity")
                optimized = True
                continue
            ret.append(row)
        program = ret

        # todo: some merges?
    return program


def ROTR(word, m, i):
    i %= m
    mask = (1 << m) - 1
    assert 0 <= word <= mask
    return ((word >> i) | (word << (m - i))) & mask


def ROTL(word, m, i):
    return ROTR(word, m, m-i%m)


class Shuffle(list):
    """Wrapper for a permutation (with possible duplicates)"""

    def __init__(self, *args, **kwargs):
        self.input_size = kwargs.pop("input_size", None)
        super().__init__(*args, **kwargs)
        if self.input_size is None:
            self.input_size = len(self)
        assert 0 <= min(self) <= max(self) < self.input_size
        assert 0 < len(self)

    @property
    def n(self):
        """Length of the permutation"""
        return len(self)

    @property
    def m(self):
        """Log2 of the length of the permutation"""
        return log2exact(self.n)

    def _compose1(self, g):
        assert type(self) == type(g)
        return type(self)(self[i] for i in g)

    def compose(self, *args):
        if not args:
            return self
        return self._compose1(args[0].compose(args[1:]))

    __matmul__  = _compose1

    def __invert__(self):
        ip = [None] * self.n
        for i, j in enumerate(self):
            ip[j] = i
        assert None not in ip
        return type(self)(ip)

    def apply(self, pi=None):
        if pi is None:
            pi = list(range(len(self)))
        else:
            pi = list(pi)
        # assert len(pi) == len(self)
        return tuple(pi[i] for i in self)

    @classmethod
    def make_index_ROTR(cls, m, s):
        """Create a shuffle rotating m-bit indices by i to the right."""
        return cls([ROTL(i, m, s) for i in range(2**m)])

    @classmethod
    def make_index_ROTL(cls, m, s):
        """Create a shuffle rotating m-bit indices by i to the left."""
        return cls([ROTR(i, m, s) for i in range(2**m)])



class PublicShuffle(Shuffle):
    """Wrapper for a public permutation (wirings between MI)."""


class SecretShuffle(Shuffle):
    """Wrapper for a secret permutation (has to be inside MI)."""


class SecretShuffles(dict):
    """Wrapper for a list of parallel SecretShuffle's.

    Dict of form: {offset: SecretShuffle}
    """


def composeinv(c,pi):
    return [y for x, y in sorted(zip(pi, c))]


def log2exact(n):
    m = int(n).bit_length() - 1
    assert n == 1 << m
    return m


class Compiler:
    def __init__(self, f):
        self.n = len(f)
        self.m = log2exact(self.n)

        self.f = tuple(map(int, f))
        self._compile()

    def _compile(self):
        raise NotImplementedError()

    def apply(self, f : tuple=None) -> tuple:
        """Apply function to the input."""
        if f is None:
            f = list(range(self.n))
        else:
            f = list(f)
        assert len(f) == self.n
        return tuple(self._apply(f))

    def _apply(self, f):
        raise NotImplementedError()


class CompilerMI(Compiler):
    def __init__(self, f: tuple, le: int):
        self.le = int(le)
        self.l = 2**self.le
        assert le >= 1
        super().__init__(f)


class BenesPerm(Compiler):
    cols: Tuple[Tuple[int]]

    def _compile(self):
        pi = self.f
        if self.m == 1:
            # 0, 1 => no swap
            # 1, 0 => swap
            self.cols = [[pi[0]]]
            return

        # code by Bernstein ( Verified fast formulas for control bits for permutation networks https://cr.yp.to/papers.html#controlbits )
        # slightly modified
        p = [pi[x^1] for x in range(self.n)]
        q = [pi[x]^1 for x in range(self.n)]

        piinv = composeinv(range(self.n),pi)
        p,q = composeinv(p,q),composeinv(q,p)

        c = [min(x,p[x]) for x in range(self.n)]
        p,q = composeinv(p,q),composeinv(q,p)
        for _ in range(1, self.m-1):
            cp,p,q = composeinv(c,q),composeinv(p,q),composeinv(q,p)
            c = [min(c[x],cp[x]) for x in range(self.n)]

        f = [c[2*j]%2 for j in range(self.n//2)]
        F = [x^f[x//2] for x in range(self.n)]
        Fpi = composeinv(F,piinv)
        l = [Fpi[2*k]%2 for k in range(self.n//2)]
        L = [y^l[y//2] for y in range(self.n)]
        M = composeinv(Fpi,L)
        subM = [[M[2*j+e]//2 for j in range(self.n//2)] for e in range(2)]
        subz = [BenesPerm(sub).cols for sub in subM]

        z = []
        for s0, s1 in zip(*subz):
            cur = [None] * (len(s0) + len(s1))
            cur[0::2] = s0
            cur[1::2] = s1
            z.append(cur)

        self.cols = [f] + z + [l]

    def _apply(self, f):
        for i, col in enumerate(self.cols):
            ibit = min(i, 2*self.m-2-i)
            f = self.apply_col(f, self.m, ibit, col)
        return tuple(f)

    @classmethod
    def apply_col(cls, pi, m, ibit, col):
        pi = list(pi)
        assert len(pi) == 2**m

        bit = 1 << ibit

        # iterate over submasks of 111011
        # where 0 is the current active bit
        # reverse order, so can just pop from the control bits list
        j = mask = (1 << m) - 1 - bit
        col = list(col)
        while True:
            if col.pop():
                pi[j], pi[j ^ bit] = pi[j ^ bit], pi[j]
            j = (j - 1) & mask
            if j == mask:
                break
        return pi


class BenesPermMI(CompilerMI):
    """Compiles permutations into Benes networks and groups them into MultiInstructions.

    Arguments
    ---------
    f: tuple
        permutation to compile
    le: int
        group size logarithm (MI input/output size logarithm)
    """
    last_apply_MI_count : int
    last_compile_MI_count : int

    def _compile(self):
        self.last_compile_MI_count = 0
        if self.le >= self.m:
            # full permutation in one MI
            self.last_compile_MI_count = 1
            self.cols = [SecretShuffles({0: SecretShuffle(self.f)})]
            return

        assert self.n % self.l == 0
        assert self.le < self.m

        cols = BenesPerm(self.f).cols
        assert len(cols) == 2*self.m-1
        assert all(len(col) == self.n//2 for col in cols)

        # [...] [midl .. midr] [...]
        midl = self.m - self.le
        midr = self.m + self.le - 2

        result = []
        icols = [
            (min(i, 2*self.m-2-i), col)
            for i, col in enumerate(cols)
        ]

        # prefix
        for i in range(0, midl, self.le):
            sub_icols = icols[:midl][i:i+self.le]
            sub = self._compile_cols(sub_icols, width=len(sub_icols))
            self._add_to_result(result, *sub)

        # middle
        mid_icols = icols[midl:midr+1]
        sub = self._compile_cols(mid_icols, width=self.le)
        self._add_to_result(result, *sub)

        # suffix
        for i in range(midr+1, 2*self.m-1, self.le):
            sub_icols = icols[i:i+self.le]
            sub = self._compile_cols(sub_icols, width=len(sub_icols))
            self._add_to_result(result, *sub)

        self.cols = result

    def _add_to_result(self, result, inp, main, out):
        assert isinstance(inp, PublicShuffle)
        assert isinstance(out, PublicShuffle)
        assert isinstance(main, SecretShuffles)
        assert all(isinstance(g, SecretShuffle) for g in main.values())

        if result:
            result[-1] = inp @ result[-1]
        else:
            result.append(inp)
        result.append(main)
        result.append(out)

    def _compile_cols(self, icols, width):
        shift = min(i for i, col in icols)
        sink = PublicShuffle.make_index_ROTL(self.m, shift)
        lift = ~sink

        mid = list(range(self.n))
        for ibit, col in icols:
            mid = BenesPerm.apply_col(mid, self.m, ibit, col)
        mid = sink @ PublicShuffle(mid) @ lift

        mid_groups = []
        window = max(2**width, 2**self.le)
        for i in range(0, self.n, window):
            group = SecretShuffle([v - i for v in mid[i:i+window]])
            mid_groups.append((i, group))
            self.last_compile_MI_count += 1
        return lift, SecretShuffles(mid_groups), sink

    def _apply(self, f):
        self.last_apply_MI_count = 0

        for col in self.cols:
            if isinstance(col, PublicShuffle):
                f = col.apply(f)
            elif isinstance(col, SecretShuffles):
                assert all(isinstance(v, SecretShuffle) for v in col.values())
                f2 = []
                off = 0
                for off2, sub in col.items():
                    assert off2 == off
                    f2.extend(sub.apply(f[off:off+len(sub)]))
                    off += len(sub)
                    self.last_apply_MI_count += 1
                assert off == len(f) == len(f2)
                f = f2
                del f2
            else:
                raise NotImplementedError()
        return tuple(f)

    def canonical(self):
        return list(self.cols)


class ForwardDupLowDepth(Compiler):
    cols: Tuple[Tuple[int]]

    def _compile(self):
        f = self.f
        cols = []
        for h in range(self.m):
            col = []
            step = 2**h
            for i in range(2**self.m - step):
                col.append(int(f[i+step] == f[i]))
            cols.append(col)
        self.cols = tuple(map(tuple, cols))

    def _apply(self, f):
        for h, col in enumerate(self.cols):
            step = 2**h
            for i in range(2**self.m - step):
                f[i+step] = f[i] if col[i] else f[i+step]
        return tuple(f)

    def canonical(self):
        return list(self.cols)


class ForwardDup(Compiler):
    cols: Tuple[Tuple[int]]

    def _compile(self):
        self.col = tuple(
            int(self.f[i] == self.f[i-1])
            for i in range(1, self.n)
        )

    def _apply(self, f):
        for i, flag in enumerate(self.col):
            f[i+1] = f[i] if flag else f[i+1]
        return tuple(f)


class ForwardDupMI(CompilerMI):
    cols: List[SecretShuffles]

    last_apply_MI_count : int
    last_compile_MI_count : int

    @staticmethod
    def clean_f(f):
        ff = [0]
        for i in range(1, len(f)):
            if f[i] == f[i-1]:
                ff.append(ff[-1])
            else:
                ff.append(i)
        return ff

    def _compile(self):
        self.last_compile_MI_count = 0
        if self.le >= self.m:
            sub = self.clean_f(self.f)
            self.last_compile_MI_count = 1
            self.cols = [SecretShuffles({0: SecretShuffle(sub, input_size=len(sub))})]
            return

        sub = self.clean_f(self.f[:self.l])
        cols = [
            {0: SecretShuffle(sub, input_size=len(sub))}
        ]
        self.last_compile_MI_count += 1

        step = off = self.l - 1
        while off < self.n - 1:
            sub = self.clean_f(self.f[off:off+step+1])
            assert len(sub) > 1
            cols.append({
                off: SecretShuffle(sub, input_size=len(sub))
            })
            self.last_compile_MI_count += 1
            off += step
        self.cols = list(map(SecretShuffles, cols))

    def _apply(self, f):
        self.last_apply_MI_count = 0
        ff = list(f)
        for sss in self.cols:
            for off, ss in sss.items():
                sub = ff[off:off+ss.input_size]
                assert ss.input_size > 1
                self.last_apply_MI_count += 1
                sub = ss.apply(sub)
                ff[off:off+len(sub)] = sub
        assert len(ff) == len(f), (len(f), len(ff))
        return tuple(ff)

    def canonical(self):
        return list(self.cols)


class BDBFunc(Compiler):
    PERM_CLASS = BenesPerm
    FW_DUP_CLASS = ForwardDup

    input_perm : BenesPerm
    output_perm : BenesPerm
    dups: ForwardDup

    def _compile(self):
        f = self.f
        pos = defaultdict(list)
        for i, a in enumerate(f):
            pos[a].append(i)
        missing = set(range(len(f))) - set(f)

        pi = []
        pi2 = [None] * self.n
        pif = []
        start = defaultdict(int)
        for a, cs in pos.items():
            cs = list(cs)
            c = len(cs)
            start[a] = len(pi)
            pi.append(a)
            pif += [a] * c
            pi2[cs.pop()] = a
            for i in range(c - 1):
                a = missing.pop()
                pi.append(a)
                pi2[cs.pop()] = a

        pi2 = []
        for a in f:
            pi2.append(start[a])
            start[a] += 1

        self._compile_finish(pi, pif, pi2)

    def _compile_finish(self, pi, pif, pi2):
        self.input_perm = self.PERM_CLASS(pi)
        self.output_perm = self.PERM_CLASS(pi2)
        self.dups = self.FW_DUP_CLASS(pif)

    def _apply(self, f):
        f = self.input_perm.apply(f)
        f = self.dups.apply(f)
        f = self.output_perm.apply(f)
        return f


class BDBFuncMI(BDBFunc, CompilerMI):
    """Benes-Duplicates-Benes method for implementing function with MultiInstructions."""
    PERM_CLASS = BenesPermMI
    FW_DUP_CLASS = ForwardDupMI

    def _compile_finish(self, pi, pif, pi2):
        self.input_perm = self.PERM_CLASS(pi, le=self.le)
        self.output_perm = self.PERM_CLASS(pi2, le=self.le)
        self.dups = self.FW_DUP_CLASS(pif, le=self.le)

    def canonical(self):
        res = self.input_perm.canonical()
        res += self.dups.canonical()
        res += self.output_perm.canonical()
        return res


def test():
    for m in range(1, 8):
        print("m =", m)

        for _ in range(10):
            f = list(range(2**m))
            shuffle(f)

            assert tuple(f) == BenesPerm(f).apply()
            assert tuple(f) == BDBFunc(f).apply()

            f = [randrange(2**m) for _ in range(2**m)]
            assert tuple(f) == BDBFunc(f).apply()

            f = [randrange(2**m)] * 2**m
            assert tuple(f) == BDBFunc(f).apply()

            f = list(range(2**m))
            shuffle(f)

            for le in range(1, m+2):
                assert tuple(f) == BenesPermMI(f, le=le).apply()

            f = [randrange(2**m) for _ in range(2**m)]

            for le in range(1, m+2):
                assert tuple(f) == BDBFuncMI(f, le=le).apply()

    print("tests ok")


def test2():
    m = 5
    f = list(range(2**m))
    shuffle(f)

    for le in range(1, m+2):
        bp = BenesPermMI(f, le=le)
        ff = bp.apply()
        assert tuple(f) == ff
        assert bp.last_compile_MI_count == bp.last_apply_MI_count

        dup = ForwardDupMI(f, le=le)
        ff = dup.apply()
        assert dup.last_compile_MI_count == dup.last_apply_MI_count

        print(
            f"{m=:2d} {le=:2d} MI count: Benes {bp.last_compile_MI_count:5d} Dup {dup.last_compile_MI_count:3d}"
            f" Total: {bp.last_compile_MI_count*2+dup.last_compile_MI_count}")

    m = 4
    le = 2
    f = [0]
    for i in range(2**m-1):
        if randrange(2):
            f.append(f[-1])
        else:
            f.append(i+1)
    dup = ForwardDupMI(f, le=le)
    ff = dup.apply()
    assert tuple(f) == tuple(ff)


if __name__ == '__main__':
    example()
    # test()
    # test2()
