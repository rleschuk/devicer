

def parse_tuple(s):
    if s.startswith('(') and s.endswith(')'):
        try: return eval(s)
        except: pass
    return (s,)
