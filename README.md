# news-image-20261122-v6

One image summing up the world news of **Sunday 22 November 2026**.

[![make.fun · news-image-20261122](https://make.fun/badge/news-image-20261122.svg)](https://make.fun/bounty/news-image-20261122?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122)

[![rank](https://make.fun/badge/news-image-20261122/Misaka450/news-image-20261122-v6/rank.svg)](https://make.fun/bounty/news-image-20261122/leaderboard)
[![reward](https://make.fun/badge/news-image-20261122/Misaka450/news-image-20261122-v6/reward.svg)](https://make.fun/bounty/news-image-20261122)

26 stories across seven regions, every one dated and every one illustrated:
14 lead cards with drawings, 12 briefs with icons, a six-cell ledger of the day's
numbers, a UTC timeline, a pinned world map, and a date-check strip naming what
was left out and why.

## Run

```bash
python3 build.py     # writes entry.png and preview-300.png (1024x1024, <=1 MiB)
node main.ts         # copies entry.png to $MAKEFUN_OUTPUT_DIR/entry.png
```

No network, no image models: everything is drawn with Pillow.

## License

MIT
