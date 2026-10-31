# Retail Customer Insights

[Back to my profile](../../README.md)

## Introduction

I built this case study to practise working with transactional data from cleaning through to analysis. It uses the historical UCI Online Retail dataset and presents the results in Streamlit.

## Problem

Understand sales patterns and customer behaviour while making the cleaning rules and limits of the dataset visible.

## My role

Data cleaning, metric definitions, SQL analysis and dashboard presentation.

## Main features

- Country/date filters and sales overview
- SQL business questions and a local SQLite export
- Rule-based RFM customer segmentation
- A data-quality audit and documented metric definitions

## Stack

Python, pandas, SQLite, Plotly, Streamlit

## Demo or walkthrough

[Open the demo](https://retail-customer-insights.streamlit.app/)

This is the deployment linked by the project repository. Its current availability has not been re-tested for this profile release.

## Learning focus

These notes describe the concepts I am practising in the implementation.

- Defining metrics and cleaning rules before building charts.
- Keeping missing customer IDs separate from transaction-level sales.

## Status and outcome

**Historical portfolio case study**

A dashboard, reproducible cleaning rules, SQL queries and documented limitations.

## Limits

- The data is from 2010-2011.
- Revenue from retained positive sales is not profit or net revenue after returns.
- RFM segments are descriptive rules, not a trained churn model.

## Source

[Repository](https://github.com/NhatNguyen2407/retail-customer-insights) - [Project README](https://github.com/NhatNguyen2407/retail-customer-insights/blob/main/README.md)
