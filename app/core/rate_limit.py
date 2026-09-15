from slowapi import Limiter
from slowapi.util import get_remote_address

# Keyed by client IP, in-memory storage. This is only correct for a single
# backend instance (see README "Known limitations") — if this ever runs behind
# multiple instances/replicas, swap in a Redis-backed storage_uri here.
limiter = Limiter(key_func=get_remote_address)
