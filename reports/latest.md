## pull-official
E2025: 402 games played, 0 box scores fetched now
E2026: 70 games played, 0 box scores fetched now

## pull-platform
pulled -> 
/home/runner/work/euroleague-fantasy-agent/euroleague-fantasy-agent/data/raw/fan
taking/md_08
team: UnderTakers86  credits: 105.9  trades used: 0/4

## build
        games  rows  mismatches
season                         
E2025     402  9540           0
E2026      70  1678           0
teams mapped: 20; needs attention: 1
platform_abbr     platform_name official_code     official_name                 
method
          BJK Besiktas Istanbul           BES Besiktas Istanbul name (seed BJK 
disagreed)
method
surname+team    279
UNMATCHED        79

## reconcile
Traceback (most recent call last):
  File "/opt/hostedtoolcache/Python/3.12.15/x64/bin/elfa", line 6, in <module>
    sys.exit(app())
             ^^^^^
  File "/opt/hostedtoolcache/Python/3.12.15/x64/lib/python3.12/site-packages/typer/main.py", line 1154, in __call__
    raise e
  File "/opt/hostedtoolcache/Python/3.12.15/x64/lib/python3.12/site-packages/typer/main.py", line 1137, in __call__
    return get_command(self)(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.12.15/x64/lib/python3.12/site-packages/typer/_click/core.py", line 802, in __call__
    return self.main(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.12.15/x64/lib/python3.12/site-packages/typer/core.py", line 1197, in main
    return _main(
           ^^^^^^
  File "/opt/hostedtoolcache/Python/3.12.15/x64/lib/python3.12/site-packages/typer/core.py", line 187, in _main
    rv = self.invoke(ctx)
         ^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.12.15/x64/lib/python3.12/site-packages/typer/core.py", line 1119, in invoke
    return _process_result(sub_ctx.command.invoke(sub_ctx))
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.12.15/x64/lib/python3.12/site-packages/typer/_click/core.py", line 741, in invoke
    return ctx.invoke(self.callback, **ctx.params)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.12.15/x64/lib/python3.12/site-packages/typer/_click/core.py", line 483, in invoke
    return callback(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.12.15/x64/lib/python3.12/site-packages/typer/main.py", line 1524, in wrapper
    return callback(**use_params)
           ^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/euroleague-fantasy-agent/euroleague-fantasy-agent/src/elfa/cli.py", line 74, in reconcile
    rprint(gate_report(_rec()))
           ^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/euroleague-fantasy-agent/euroleague-fantasy-agent/src/elfa/model/reconcile.py", line 60, in gate_report
    counts = df.status.value_counts().to_dict()
             ^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.12.15/x64/lib/python3.12/site-packages/pandas/core/generic.py", line 6434, in __getattr__
    return object.__getattribute__(self, name)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'DataFrame' object has no attribute 'status'
