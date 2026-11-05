def in_known_scope(membership, boundaries):
    """Only skip VM-backed identity reads for an already pinned, populated scope."""
    return any(membership == '0::'+path or membership.startswith('0::'+path+'/')
               for path in boundaries)
