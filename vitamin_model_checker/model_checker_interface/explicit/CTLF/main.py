import re
import heapq

# -------------------------------------------------------------------
# 1) FKS and fuzzy operations
# -------------------------------------------------------------------
class FKS:
    def __init__(self, states, initial, R, V):
        self.states = states
        self.initial = initial
        self.R = R
        self.V = V

    def post(self, s):
        return self.R.get(s, {})

class FuzzyOps:
    def __init__(self, t_norm, t_conorm, neg, impl):
        self.and_ = t_norm
        self.or_  = t_conorm
        self.not_ = neg
        self.imp_ = impl

# Zadeh fuzzy logic by default
default_ops = FuzzyOps(
    t_norm=lambda x,y: min(x,y),
    t_conorm=lambda x,y: max(x,y),
    neg=lambda x: 1-x,
    impl=lambda x,y: max(1-x,y)
)

# -------------------------------------------------------------------
# 2) AST node
# -------------------------------------------------------------------
class ASTNode:
    def __init__(self, op=None, atom=None):
        self.op = op
        self.atom = atom
        self.left = None
        self.right = None
    def is_atom(self):
        return self.atom is not None

# -------------------------------------------------------------------
# 3) Fuzzy-CTL operators (EX, AX, EU, EG, AU, AF, AG, AND, OR, IMPLIES, NOT)
# -------------------------------------------------------------------
def ex(fks, phi, ops):
    return {
        s: max((ops.and_(r, phi.get(s2,0.0)) for s2,r in fks.post(s).items()), default=0.0)
        for s in fks.states
    }

def ax(fks, phi, ops):
    out={}
    for s in fks.states:
        succ=fks.post(s)
        out[s] = (1.0 if not succ else
                  min(ops.and_(r, phi.get(s2,0.0)) for s2,r in succ.items()))
    return out

def eu(fks, phi, psi, ops):
    v = dict(psi)
    for _ in fks.states:
        v_new = v.copy()
        for s in fks.states:
            nxt = max((ops.and_(r, v[s2]) for s2,r in fks.post(s).items()), default=0.0)
            v_new[s] = ops.or_(v[s], ops.and_(phi.get(s,0.0), nxt))
        v = v_new
    return v

def eg(fks, phi, ops):
    v = {s:1.0 for s in fks.states}
    while True:
        nxt = ex(fks, v, ops)
        v_new = {s:ops.and_(phi.get(s,0.0), nxt[s]) for s in fks.states}
        if v_new == v: break
        v = v_new
    return v

def au(fks, phi, psi, ops):
    v = dict(psi)
    w = {s:1.0 for s in fks.states}
    count = {s:len(fks.post(s)) for s in fks.states}
    T = set(fks.states)
    heap = [(-v[s],s) for s in fks.states]
    heapq.heapify(heap)
    while T:
        while True:
            val,s = heapq.heappop(heap)
            if s in T and -val==v[s]:
                break
        T.remove(s)
        for t in list(T):
            if s in fks.post(t):
                r = fks.post(t)[s]
                w[t] = min(w[t], ops.and_(phi.get(t,0.0), ops.and_(r, v[s])))
                count[t] -= 1
                if count[t]==0:
                    new = max(v[t], w[t])
                    if new>v[t]:
                        v[t] = new
                        heapq.heappush(heap,(-v[t],t))
    return v

def solve_fctl(node, fks, ops=default_ops):
    if node.is_atom():
        return {s: fks.V[s].get(node.atom,0.0) for s in fks.states}

    op = node.op
    if op == 'NOT':
        φ = solve_fctl(node.left, fks, ops)
        return {s: ops.not_(φ[s]) for s in fks.states}
    if op == 'EX':   return ex(fks,   solve_fctl(node.left,fks,ops), ops)
    if op == 'AX':   return ax(fks,   solve_fctl(node.left,fks,ops), ops)
    if op == 'EU':
        return eu(fks,
                  solve_fctl(node.left,fks,ops),
                  solve_fctl(node.right,fks,ops),
                  ops)
    if op == 'AU':
        return au(fks,
                  solve_fctl(node.left,fks,ops),
                  solve_fctl(node.right,fks,ops),
                  ops)
    if op == 'EG':   return eg(fks,  solve_fctl(node.left,fks,ops), ops)
    if op == 'EF':
        return eu(fks,
                  {s:1.0 for s in fks.states},
                  solve_fctl(node.left,fks,ops),
                  ops)
    if op == 'AF':
        φ_map = solve_fctl(node.left,fks,ops)
        not_φ = {s: ops.not_(φ_map[s]) for s in fks.states}
        eg_not = eg(fks, not_φ, ops)
        return {s: ops.not_(eg_not[s]) for s in fks.states}
    if op == 'AG':
        φ_map = solve_fctl(node.left,fks,ops)
        not_φ = {s: ops.not_(φ_map[s]) for s in fks.states}
        eu_not = eu(fks, not_φ, {s:1.0 for s in fks.states}, ops)
        return {s: ops.not_(eu_not[s]) for s in fks.states}
    if op in ('AND','OR','IMPLIES'):
        φ = solve_fctl(node.left, fks, ops)
        ψ = solve_fctl(node.right,fks,ops)
        if op=='AND':    return {s: ops.and_(φ[s],ψ[s]) for s in fks.states}
        if op=='OR':     return {s: ops.or_(φ[s],ψ[s])  for s in fks.states}
        return {s: ops.imp_(φ[s],ψ[s]) for s in fks.states}

    raise NotImplementedError(f"Operator {op} not supported")

# -------------------------------------------------------------------
# 4) Parser utilities
# -------------------------------------------------------------------
def tokenize(formula):
    return re.findall(
      r"EX|AX|EU|AU|EF|AF|EG|AG|AND|OR|IMPLIES|NOT|\(|\)|[a-zA-Z_][a-zA-Z0-9_]*",
      formula)

class Parser:
    def __init__(self,toks):  self.toks,self.pos = toks,0
    def peek(self):           return self.toks[self.pos] if self.pos<len(self.toks) else None
    def consume(self,x=None):
        tok=self.peek()
        if x and tok!=x: raise SyntaxError(f"Expected {x}, got {tok}")
        self.pos+=1; return tok
    def parse(self): return self._imp()
    def _imp(self):
        node=self._or()
        while self.peek()=='IMPLIES':
            self.consume('IMPLIES'); right=self._or()
            p=ASTNode('IMPLIES'); p.left,p.right=node,right; node=p
        return node
    def _or(self):
        node=self._and()
        while self.peek()=='OR':
            self.consume('OR'); right=self._and()
            p=ASTNode('OR'); p.left,p.right=node,right; node=p
        return node
    def _and(self):
        node=self._un()
        while self.peek()=='AND':
            self.consume('AND'); right=self._un()
            p=ASTNode('AND'); p.left,p.right=node,right; node=p
        return node
    def _un(self):
        tok=self.peek()
        if tok=='NOT':
            self.consume('NOT'); n=ASTNode('NOT'); n.left=self._un(); return n
        if tok in ('EX','AX','EF','AF','EG','AG'):
            op=self.consume(); n=ASTNode(op); n.left=self._un(); return n
        if tok in ('EU','AU'):
            op=self.consume(); self.consume('(')
            l=self.parse(); self.consume(','); r=self.parse(); self.consume(')')
            n=ASTNode(op); n.left,n.right=l,r; return n
        if tok=='(':
            self.consume('('); n=self.parse(); self.consume(')'); return n
        return ASTNode(atom=self.consume())

def parse_formula(s): return Parser(tokenize(s)).parse()


# -------------------------------------------------------------------
# 5) parse model (fuzzy transitions via action→degree mapping)
# -------------------------------------------------------------------
def parse_model(path):
    lines = [l.strip() for l in open(path) if l.strip()]

    # 1) Stati reali e numero
    states = lines[lines.index('Name_State')+1].split()
    N = len(states)

    # 2) Blocchetto Transition
    t0 = lines.index('Transition') + 1
    te = (lines.index('Unkown_Transition_by')
          if 'Unkown_Transition_by' in lines
          else lines.index('Name_State'))
    t_lines = lines[t0:te]
    if len(t_lines) < N:
        raise ValueError(f"Attesi ≥{N} righe di Transition, trovate {len(t_lines)}")

    # 3) Raccogli etichette azioni
    labels = set()
    for line in t_lines[:N]:
        toks = re.split(r'\s+', line)
        for cell in toks:
            if cell!='0':
                labels.add(cell)
    labels = sorted(labels)
    # assegna degree uniformi in (0,1)
    M = len(labels)
    action_degree = {
        lab: (i+1)/(M+1)
        for i,lab in enumerate(labels)
    }

    # 4) Costruisci R fuzzy
    R = {s:{} for s in states}
    for i,line in enumerate(t_lines[:N]):
        toks = re.split(r'\s+', line)
        if len(toks)!=N:
            raise ValueError(f"Line {i} of Transition has {len(toks)} cols, need {N}")
        for j,cell in enumerate(toks):
            if cell=='0': continue
            # mappa label→degree
            deg = action_degree.get(cell, 0.0)
            if deg>0: R[states[i]][states[j]] = deg

    # 5) Initial state
    init = lines[lines.index('Initial_State')+1].strip()

    # 6) Atomic props
    AP = lines[lines.index('Atomic_propositions')+1].split()

    # 7) Labelling
    l0 = lines.index('Labelling')+1
    lab_lines = lines[l0:l0+N]
    if len(lab_lines)<N:
        raise ValueError(f"Attesi {N} lab lines, trovate {len(lab_lines)}")
    V={}
    for i,s in enumerate(states):
        vals = lab_lines[i].split()
        if len(vals)!=len(AP):
            raise ValueError(f"Labelling riga {i} ha {len(vals)} val, servono {len(AP)}")
        V[s] = {AP[k]:float(vals[k]) for k in range(len(AP))}

    return FKS(states, init, R, V)


# -------------------------------------------------------------------
# 6) main
# -------------------------------------------------------------------
if __name__ == '__main__':
    model_path = 'C:\\Users\\utente\\Desktop\\Lavoro\\NatATL-Tool\\RecallNatATL\\Testing\\exampleModel.txt'
    formula_str = 'EXa'

    fks = parse_model(model_path)
    ast = parse_formula(formula_str)
    res = solve_fctl(ast, fks)

    print("Action→degree mapping:")
    for s in fks.states:
        for t, deg in fks.R[s].items():
            print(f"  {s} → {t}: {deg:.1f}")

    print("\nGrado di soddisfazione per ogni stato:")
    for s in fks.states:
        print(f"  {s}: {res[s]:.1f}")
    print(f"\nInitial state '{fks.initial}' → {res[fks.initial]:.1f}")
    print(res)
