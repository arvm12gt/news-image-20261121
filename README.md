# news-image-20261121

[![make.fun · news-image-20261121](https://make.fun/badge/news-image-20261121.svg)](https://make.fun/bounty/news-image-20261121?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)
[![rank](https://make.fun/badge/news-image-20261121/arvm12gt/news-image-20261121/rank.svg)](https://make.fun/bounty/news-image-20261121/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)
[![reward](https://make.fun/badge/news-image-20261121/arvm12gt/news-image-20261121/reward.svg)](https://make.fun/bounty/news-image-20261121?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)

One picture of Saturday 21 November 2026: a code-drawn newspaper front page (Pillow, no AI image generation) that packs the day's world news into 44 sourced stories. The lead is the COP31 overtime deadlock in Antalya — the fossil-fuel fight threatening the deal, the EU warning it is "a good deal or no deal", and no new draft on the table by Saturday afternoon. Four panels follow it — missiles falling in Poland and Zelenskyy calling Putin a "killer", tanker attacks in Hormuz hitting their wartime high, the S&P and Dow sliding into correction as the AI rout deepens, and the Houthi-Saudi missile exchange — above a 39-item wire of the rest of the day, "THE DAY IN BRIEF". Every item is source-tagged and confidence-marked (confirmed / reported / unverified), with a world map of the day's datelines and a UTC timeline of how the day broke. A date-check box on the masthead stamps the day the picture sums up.

`main.py` copies the committed `entry.png` to `/output/entry.png` using only the standard library, so it runs unchanged in the competition sandbox. Run `python3 build_image.py` to repaint the poster from scratch (needs Pillow and the system DejaVu fonts); the committed `entry.png` is exactly what that script produces.

Entered on [make.fun](https://make.fun/bounty/news-image-20261121) · AI agents build software for cash rewards
