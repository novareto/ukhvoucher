from math import log


def get_dichotomy_batches(N, n):
    """
    A dummy batch object::

      >>> batch = range(1, 101)  # have enough numbers

    Help user make a dichotomic search::

      >>> list(get_dichotomy_batches(batch, 100,50))
      [('previous', 1), ('ellipsis', '...'), ('previous', 25), ('ellipsis', '...'), ('previous', 48), ('previous', 49), ('current', 50), ('next', 51), ('next', 52), ('ellipsis', '...'), ('next', 75), ('ellipsis', '...'), ('next', 100)]
      >>> list(get_dichotomy_batches(batch, 100,25))
      [('previous', 1), ('ellipsis', '...'), ('previous', 12), ('ellipsis', '...'), ('previous', 24), ('current', 25), ('next', 26), ('ellipsis', '...'), ('next', 37), ('ellipsis', '...'), ('next', 50), ('ellipsis', '...'), ('next', 100)]

    limit cases::

      >>> list(get_dichotomy_batches(batch, 1,1))
      [('current', 1)]
      >>> list(get_dichotomy_batches(batch, 100,1))
      [('current', 1), ('next', 2), ('next', 3), ('ellipsis', '...'), ('next', 6), ('ellipsis', '...'), ('next', 12), ('ellipsis', '...'), ('next', 25), ('ellipsis', '...'), ('next', 50), ('ellipsis', '...'), ('next', 100)]
      >>> list(get_dichotomy_batches(batch, 100,1))
      [('current', 1), ('next', 2), ('next', 3), ('ellipsis', '...'), ('next', 6), ('ellipsis', '...'), ('next', 12), ('ellipsis', '...'), ('next', 25), ('ellipsis', '...'), ('next', 50), ('ellipsis', '...'), ('next', 100)]

    Buggy cases do not break::
    >>> list(get_dichotomy_batches(batch, 100,150)) == (
    ...     list(get_dichotomy_batches(batch, 100,100)))
    True
    >>> list(get_dichotomy_batches(batch, 100,-20)) == (
    ...     list(get_dichotomy_batches(batch, 100,1)))
    True
    
    """
    # normalize
    n = max(1, min(n, N))
    if not n:
        n = 1
    # number of iteration to find n doing a dichotomic search in 1..N
    log_position = int(log(max(N/n, 1), 2))

    markers = set([1, max(1, n-1), n, min(n+1, N), N])
    # always middle
    markers.add(int(N/2))
    # previous numbers in a dichotomich search
    for i in range(log_position)[-2:]:
        markers.add(int(N / 2**i))
    # next numbers  in a dichotomich search
    i = int(N / 2**(log_position+1))
    markers.add(i)
    markers.add(min(n + i, N))

    for i in range(log_position, ):
        markers.add(int(N / 2**i))

    # if we have less than 8 buttons, add some around current
    maxlen = min(8, N)  # maybe N < 8 !
    i = 2
    while len(markers) < maxlen:
        markers.add(min(n+i, N))
        markers.add(max(n-i, 1))
        i += 1
    markers = list(markers)
    markers.sort()

    last = 0
    for b in markers:
        if b and b > last:
            if last and b > last + 1:
                yield 'ellipsis', '...'
            if b == n:
                yield 'current', b
            elif b > n:
                yield 'next', b
            else:
                yield 'previous', b

            last = b
