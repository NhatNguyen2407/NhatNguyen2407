# World Cup Player Analytics

[Back to my profile](../../README.md)

## Introduction

I built a small dashboard to explore player event statistics from the 2022 World Cup. It loads StatsBomb Open Data and compares players within one selected match.

## Problem

Turn event records into understandable player summaries without overstating what those records can measure.

## My role

Event aggregation, metric definitions and interactive player comparisons.

## Main features

- Select a match from the 2022 World Cup
- Filter players by national team
- Explore goals, assists, shots, passes and pass accuracy
- Compare two players from the same match

## Stack

Python, pandas, Plotly, Streamlit, StatsBomb Open Data

## Demo or walkthrough

[Open the repository and run instructions](https://github.com/NhatNguyen2407/football-analytics)

No verified public demo is linked for this project.

## Learning focus

These notes describe the concepts I am practising in the implementation.

- Defining player metrics from event records.
- Handling zero attempts and excluding penalty-shootout events.

## Status and outcome

**Descriptive match-level dashboard**

An interactive player dashboard with documented event definitions and synthetic regression tests.

## Limits

- Metrics are for the selected match, not the whole tournament.
- The current version does not estimate verified minutes or per-90 statistics.
- It does not predict match outcomes or rank overall player quality.

## Source

[Repository](https://github.com/NhatNguyen2407/football-analytics) - [Project README](https://github.com/NhatNguyen2407/football-analytics/blob/main/README.md)
