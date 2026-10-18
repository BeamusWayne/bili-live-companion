from bilibili_drops_miner.gui import run_gui


if __name__ == "__main__":
    import sys
    if "--smoke-test" in sys.argv:
        from bilibili_drops_miner.desktop_smoke import run_desktop_smoke_test
        raise SystemExit(run_desktop_smoke_test())
    raise SystemExit(run_gui())
