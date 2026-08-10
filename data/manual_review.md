# Phase-0 项① 人工核查样本（40 对，随机种子 7）

每对检查三件事：(a) 两个候选说的是同一个 (公司, 科目, 报告期) 吗；
(b) as_of 时点下，gold 确实已披露、distractor 确实尚未披露吗；
(c) 文本里有没有任何能推断披露时间的线索。

## 1. PM / RestructuringCharges

- **query**: What was PM's Restructuring Charges for the period ended 2012-12-31?
- **as_of**: 2013-08-23   (窗口 364 天, 2 个版本)
- **GOLD**      avail=2013-02-22  PM reported Restructuring Charges of -55,000,000 USD for the period ended 2012-12-31.
- **DISTRACTOR** avail=2014-02-21  PM reported Restructuring Charges of 55,000,000 USD for the period ended 2012-12-31.
- 值差异: -5.5e+07 vs 5.5e+07

## 2. LLY / CostOfGoodsAndServicesSold

- **query**: What was LLY's Cost of Goods and Services Sold for the period ended 2018-09-30?
- **as_of**: 2019-05-01   (窗口 353 天, 2 个版本)
- **GOLD**      avail=2018-11-06  LLY reported Cost of Goods and Services Sold of 4,836,300,000 USD for the period ended 2018-09-30.
- **DISTRACTOR** avail=2019-10-25  LLY reported Cost of Goods and Services Sold of 3,551,800,000 USD for the period ended 2018-09-30.
- 值差异: 4.836e+09 vs 3.552e+09

## 3. RTX / AllowanceForDoubtfulAccountsReceivableCurrent

- **query**: What was RTX's Accounts Receivable, Allowance for Credit Loss, Current for the period ended 2019-12-31?
- **as_of**: 2020-06-17   (窗口 264 天, 3 个版本)
- **GOLD**      avail=2020-02-06  RTX reported Accounts Receivable, Allowance for Credit Loss, Current of 389,000,000 USD for the period ended 2019-12-31.
- **DISTRACTOR** avail=2020-10-27  RTX reported Accounts Receivable, Allowance for Credit Loss, Current of 254,000,000 USD for the period ended 2019-12-31.
- 值差异: 3.89e+08 vs 2.54e+08

## 4. META / UndistributedEarningsLossAllocatedToParticipatingSecuritiesBasic

- **query**: What was META's Undistributed Earnings (Loss) Allocated to Participating Securities, Basic for the period ended 2016-06-30?
- **as_of**: 2017-01-26   (窗口 364 天, 2 个版本)
- **GOLD**      avail=2016-07-28  META reported Undistributed Earnings (Loss) Allocated to Participating Securities, Basic of 12,000,000 USD for the period ended 2016-06-30.
- **DISTRACTOR** avail=2017-07-27  META reported Undistributed Earnings (Loss) Allocated to Participating Securities, Basic of 13,000,000 USD for the period ended 2016-06-30.
- 值差异: 1.2e+07 vs 1.3e+07

## 5. JPM / NetIncomeLossAvailableToCommonStockholdersBasic

- **query**: What was JPM's Net Income (Loss) Available to Common Stockholders, Basic for the period ended 2016-06-30?
- **as_of**: 2017-02-01   (窗口 364 天, 2 个版本)
- **GOLD**      avail=2016-08-03  JPM reported Net Income (Loss) Available to Common Stockholders, Basic of 5,666,000,000 USD for the period ended 2016-06-30.
- **DISTRACTOR** avail=2017-08-02  JPM reported Net Income (Loss) Available to Common Stockholders, Basic of 5,728,000,000 USD for the period ended 2016-06-30.
- 值差异: 5.666e+09 vs 5.728e+09

## 6. PFE / IncomeLossFromDiscontinuedOperationsNetOfTaxAttributableToReportingEntity

- **query**: What was PFE's Income (Loss) from Discontinued Operations, Net of Tax, Attributable to Parent for the period ended 2021-04-04?
- **as_of**: 2021-11-10   (窗口 363 天, 2 个版本)
- **GOLD**      avail=2021-05-13  PFE reported Income (Loss) from Discontinued Operations, Net of Tax, Attributable to Parent of 9,000,000 USD for the period ended 2021-04-04.
- **DISTRACTOR** avail=2022-05-11  PFE reported Income (Loss) from Discontinued Operations, Net of Tax, Attributable to Parent of 1,000,000 USD for the period ended 2021-04-04.
- 值差异: 9e+06 vs 1e+06

## 7. JNJ / OtherComprehensiveIncomeReclassificationAdjustmentOnDerivativesIncludedInNetIncomeNetOfTax

- **query**: What was JNJ's Other Comprehensive Income (Loss), Reclassification Adjustment on Derivatives Included in Net Income, Net of Tax for the period ended 2011-10-02?
- **as_of**: 2012-05-09   (窗口 367 天, 2 个版本)
- **GOLD**      avail=2011-11-08  JNJ reported Other Comprehensive Income (Loss), Reclassification Adjustment on Derivatives Included in Net Income, Net of Tax of -185,000,000 USD for the period ended 2011-10-02.
- **DISTRACTOR** avail=2012-11-09  JNJ reported Other Comprehensive Income (Loss), Reclassification Adjustment on Derivatives Included in Net Income, Net of Tax of 185,000,000 USD for the period ended 2011-10-02.
- 值差异: -1.85e+08 vs 1.85e+08

## 8. WFC / OtherComprehensiveIncomeLossTax

- **query**: What was WFC's Other Comprehensive Income (Loss), Tax for the period ended 2017-09-30?
- **as_of**: 2018-05-06   (窗口 368 天, 2 个版本)
- **GOLD**      avail=2017-11-03  WFC reported Other Comprehensive Income (Loss), Tax of 852,000,000 USD for the period ended 2017-09-30.
- **DISTRACTOR** avail=2018-11-06  WFC reported Other Comprehensive Income (Loss), Tax of 753,000,000 USD for the period ended 2017-09-30.
- 值差异: 8.52e+08 vs 7.53e+08

## 9. GE / IncomeLossFromContinuingOperationsPerDilutedShare

- **query**: What was GE's Income (Loss) from Continuing Operations, Per Diluted Share for the period ended 2023-12-31?
- **as_of**: 2024-08-03   (窗口 367 天, 2 个版本)
- **GOLD**      avail=2024-02-02  GE reported Income (Loss) from Continuing Operations, Per Diluted Share of 1.44 USD per share for the period ended 2023-12-31.
- **DISTRACTOR** avail=2025-02-03  GE reported Income (Loss) from Continuing Operations, Per Diluted Share of 1.08 USD per share for the period ended 2023-12-31.
- 值差异: 1.44 vs 1.08

## 10. TSLA / PaymentsForRestructuring

- **query**: What was TSLA's Payments for Restructuring for the period ended 2018-12-31?
- **as_of**: 2019-08-17   (窗口 359 天, 3 个版本)
- **GOLD**      avail=2019-02-19  TSLA reported Payments for Restructuring of 27,300,000 USD for the period ended 2018-12-31.
- **DISTRACTOR** avail=2020-02-13  TSLA reported Payments for Restructuring of 27,000,000 USD for the period ended 2018-12-31.
- 值差异: 2.73e+07 vs 2.7e+07

## 11. GS / OtherInterestAndDividendIncome

- **query**: What was GS's Other Interest and Dividend Income for the period ended 2014-09-30?
- **as_of**: 2015-05-05   (窗口 363 天, 2 个版本)
- **GOLD**      avail=2014-11-05  GS reported Other Interest and Dividend Income of 505,000,000 USD for the period ended 2014-09-30.
- **DISTRACTOR** avail=2015-11-03  GS reported Other Interest and Dividend Income of 314,000,000 USD for the period ended 2014-09-30.
- 值差异: 5.05e+08 vs 3.14e+08

## 12. CSCO / ProceedsFromPaymentsForOtherFinancingActivities

- **query**: What was CSCO's Proceeds from (Payments for) Other Financing Activities for the period ended 2014-07-26?
- **as_of**: 2015-03-10   (窗口 364 天, 3 个版本)
- **GOLD**      avail=2014-09-09  CSCO reported Proceeds from (Payments for) Other Financing Activities of -35,000,000 USD for the period ended 2014-07-26.
- **DISTRACTOR** avail=2015-09-08  CSCO reported Proceeds from (Payments for) Other Financing Activities of -15,000,000 USD for the period ended 2014-07-26.
- 值差异: -3.5e+07 vs -1.5e+07

## 13. NVDA / PreferredStockParOrStatedValuePerShare

- **query**: What was NVDA's Preferred Stock, Par or Stated Value Per Share for the period ended 2012-01-29?
- **as_of**: 2012-09-11   (窗口 364 天, 2 个版本)
- **GOLD**      avail=2012-03-13  NVDA reported Preferred Stock, Par or Stated Value Per Share of 0.01 USD per share for the period ended 2012-01-29.
- **DISTRACTOR** avail=2013-03-12  NVDA reported Preferred Stock, Par or Stated Value Per Share of 0 USD per share for the period ended 2012-01-29.
- 值差异: 0.01 vs 0

## 14. JNJ / AmortizationOfIntangibleAssets

- **query**: What was JNJ's Amortization of Intangible Assets for the period ended 2013-12-29?
- **as_of**: 2015-02-22   (窗口 733 天, 3 个版本)
- **GOLD**      avail=2014-02-21  JNJ reported Amortization of Intangible Assets of 1,363,000,000 USD for the period ended 2013-12-29.
- **DISTRACTOR** avail=2016-02-24  JNJ reported Amortization of Intangible Assets of 1,400,000,000 USD for the period ended 2013-12-29.
- 值差异: 1.363e+09 vs 1.4e+09

## 15. INTC / OtherComprehensiveIncomeDefinedBenefitPlansNetUnamortizedGainLossArisingDuringPeriodBeforeTax

- **query**: What was INTC's Other Comprehensive Income (Loss), Pension and Other Postretirement Benefit Plans, Net Unamortized Gain (Loss) Arising During Period, before Tax for the period ended 2010-12-25?
- **as_of**: 2011-08-22   (窗口 370 天, 2 个版本)
- **GOLD**      avail=2011-02-18  INTC reported Other Comprehensive Income (Loss), Pension and Other Postretirement Benefit Plans, Net Unamortized Gain (Loss) Arising During Period, before Tax of 278,000,000 USD for the period ended 2010-12-25.
- **DISTRACTOR** avail=2012-02-23  INTC reported Other Comprehensive Income (Loss), Pension and Other Postretirement Benefit Plans, Net Unamortized Gain (Loss) Arising During Period, before Tax of 300,000,000 USD for the period ended 2010-12-25.
- 值差异: 2.78e+08 vs 3e+08

## 16. RTX / OtherComprehensiveIncomeLossReclassificationAdjustmentFromAOCIPensionAndOtherPostretirementBenefitPlansTax

- **query**: What was RTX's Other Comprehensive (Income) Loss, Defined Benefit Plan, Reclassification Adjustment from AOCI, Tax for the period ended 2019-09-30?
- **as_of**: 2020-04-26   (窗口 368 天, 2 个版本)
- **GOLD**      avail=2019-10-25  RTX reported Other Comprehensive (Income) Loss, Defined Benefit Plan, Reclassification Adjustment from AOCI, Tax of 98,000,000 USD for the period ended 2019-09-30.
- **DISTRACTOR** avail=2020-10-27  RTX reported Other Comprehensive (Income) Loss, Defined Benefit Plan, Reclassification Adjustment from AOCI, Tax of -98,000,000 USD for the period ended 2019-09-30.
- 值差异: 9.8e+07 vs -9.8e+07

## 17. JPM / InterestExpenseTradingLiabilities

- **query**: What was JPM's Interest Expense, Trading Liabilities for the period ended 2017-12-31?
- **as_of**: 2019-02-26   (窗口 728 天, 3 个版本)
- **GOLD**      avail=2018-02-27  JPM reported Interest Expense, Trading Liabilities of 2,070,000,000 USD for the period ended 2017-12-31.
- **DISTRACTOR** avail=2020-02-25  JPM reported Interest Expense, Trading Liabilities of 1,669,000,000 USD for the period ended 2017-12-31.
- 值差异: 2.07e+09 vs 1.669e+09

## 18. CRM / InvestmentIncomeInterest

- **query**: What was CRM's Investment Income, Interest for the period ended 2017-07-31?
- **as_of**: 2018-02-26   (窗口 371 天, 2 个版本)
- **GOLD**      avail=2017-08-25  CRM reported Investment Income, Interest of 8,748,000 USD for the period ended 2017-07-31.
- **DISTRACTOR** avail=2018-08-31  CRM reported Investment Income, Interest of 8,000,000 USD for the period ended 2017-07-31.
- 值差异: 8.748e+06 vs 8e+06

## 19. JNJ / IncreaseDecreaseInAccountsPayableAndAccruedLiabilities

- **query**: What was JNJ's Increase (Decrease) in Accounts Payable and Accrued Liabilities for the period ended 2015-06-28?
- **as_of**: 2016-02-01   (窗口 370 天, 2 个版本)
- **GOLD**      avail=2015-07-31  JNJ reported Increase (Decrease) in Accounts Payable and Accrued Liabilities of -2,203,000,000 USD for the period ended 2015-06-28.
- **DISTRACTOR** avail=2016-08-04  JNJ reported Increase (Decrease) in Accounts Payable and Accrued Liabilities of -1,931,000,000 USD for the period ended 2015-06-28.
- 值差异: -2.203e+09 vs -1.931e+09

## 20. PFE / RestructuringCharges

- **query**: What was PFE's Restructuring Charges for the period ended 2020-12-31?
- **as_of**: 2021-08-26   (窗口 364 天, 3 个版本)
- **GOLD**      avail=2021-02-25  PFE reported Restructuring Charges of 556,000,000 USD for the period ended 2020-12-31.
- **DISTRACTOR** avail=2022-02-24  PFE reported Restructuring Charges of 535,000,000 USD for the period ended 2020-12-31.
- 值差异: 5.56e+08 vs 5.35e+08

## 21. RTX / ResearchAndDevelopmentExpense

- **query**: What was RTX's Research and Development Expense for the period ended 2017-03-31?
- **as_of**: 2017-10-27   (窗口 364 天, 2 个版本)
- **GOLD**      avail=2017-04-28  RTX reported Research and Development Expense of 577,000,000 USD for the period ended 2017-03-31.
- **DISTRACTOR** avail=2018-04-27  RTX reported Research and Development Expense of 586,000,000 USD for the period ended 2017-03-31.
- 值差异: 5.77e+08 vs 5.86e+08

## 22. TSLA / SalesRevenueGoodsNet

- **query**: What was TSLA's Sales Revenue, Goods, Net for the period ended 2016-06-30?
- **as_of**: 2017-02-03   (窗口 364 天, 2 个版本)
- **GOLD**      avail=2016-08-05  TSLA reported Sales Revenue, Goods, Net of 2,207,916,000 USD for the period ended 2016-06-30.
- **DISTRACTOR** avail=2017-08-04  TSLA reported Sales Revenue, Goods, Net of 1,932,116,000 USD for the period ended 2016-06-30.
- 值差异: 2.208e+09 vs 1.932e+09

## 23. GE / DeferredForeignIncomeTaxExpenseBenefit

- **query**: What was GE's Deferred Foreign Income Tax Expense (Benefit) for the period ended 2010-12-31?
- **as_of**: 2011-08-26   (窗口 364 天, 3 个版本)
- **GOLD**      avail=2011-02-25  GE reported Deferred Foreign Income Tax Expense (Benefit) of -1,167,000,000 USD for the period ended 2010-12-31.
- **DISTRACTOR** avail=2012-02-24  GE reported Deferred Foreign Income Tax Expense (Benefit) of 1,178,000,000 USD for the period ended 2010-12-31.
- 值差异: -1.167e+09 vs 1.178e+09

## 24. CVX / DeferredTaxAssetsInventory

- **query**: What was CVX's Deferred Tax Assets, Inventory for the period ended 2010-12-31?
- **as_of**: 2011-08-25   (窗口 364 天, 2 个版本)
- **GOLD**      avail=2011-02-24  CVX reported Deferred Tax Assets, Inventory of -483,000,000 USD for the period ended 2010-12-31.
- **DISTRACTOR** avail=2012-02-23  CVX reported Deferred Tax Assets, Inventory of 483,000,000 USD for the period ended 2010-12-31.
- 值差异: -4.83e+08 vs 4.83e+08

## 25. ABT / CostOfGoodsSold

- **query**: What was ABT's Cost of Goods Sold for the period ended 2012-03-31?
- **as_of**: 2012-11-06   (窗口 365 天, 2 个版本)
- **GOLD**      avail=2012-05-08  ABT reported Cost of Goods Sold of 3,724,921,000 USD for the period ended 2012-03-31.
- **DISTRACTOR** avail=2013-05-08  ABT reported Cost of Goods Sold of 2,359,164,000 USD for the period ended 2012-03-31.
- 值差异: 3.725e+09 vs 2.359e+09

## 26. GE / IncomeLossFromDiscontinuedOperationsNetOfTax

- **query**: What was GE's Income (Loss) from Discontinued Operations, Net of Tax, Including Portion Attributable to Noncontrolling Interest for the period ended 2011-06-30?
- **as_of**: 2012-01-28   (窗口 367 天, 2 个版本)
- **GOLD**      avail=2011-07-29  GE reported Income (Loss) from Discontinued Operations, Net of Tax, Including Portion Attributable to Noncontrolling Interest of 273,000,000 USD for the period ended 2011-06-30.
- **DISTRACTOR** avail=2012-07-30  GE reported Income (Loss) from Discontinued Operations, Net of Tax, Including Portion Attributable to Noncontrolling Interest of 229,000,000 USD for the period ended 2011-06-30.
- 值差异: 2.73e+08 vs 2.29e+08

## 27. JPM / ChangeInUnrealizedGainLossOnHedgedItemInFairValueHedge1

- **query**: What was JPM's Change in Unrealized Gain (Loss) on Hedged Item in Fair Value Hedge for the period ended 2021-09-30?
- **as_of**: 2022-05-04   (窗口 366 天, 2 个版本)
- **GOLD**      avail=2021-11-02  JPM reported Change in Unrealized Gain (Loss) on Hedged Item in Fair Value Hedge of 2,522,000,000 USD for the period ended 2021-09-30.
- **DISTRACTOR** avail=2022-11-03  JPM reported Change in Unrealized Gain (Loss) on Hedged Item in Fair Value Hedge of 1,841,000,000 USD for the period ended 2021-09-30.
- 值差异: 2.522e+09 vs 1.841e+09

## 28. GE / IncomeLossFromContinuingOperationsAttributableToNoncontrollingEntity

- **query**: What was GE's Income (Loss) from Continuing Operations, Net of Tax, Attributable to Noncontrolling Interest for the period ended 2018-06-30?
- **as_of**: 2019-01-27   (窗口 369 天, 2 个版本)
- **GOLD**      avail=2018-07-27  GE reported Income (Loss) from Continuing Operations, Net of Tax, Attributable to Noncontrolling Interest of -98,000,000 USD for the period ended 2018-06-30.
- **DISTRACTOR** avail=2019-07-31  GE reported Income (Loss) from Continuing Operations, Net of Tax, Attributable to Noncontrolling Interest of -102,000,000 USD for the period ended 2018-06-30.
- 值差异: -9.8e+07 vs -1.02e+08

## 29. GE / IncomeLossFromDiscontinuedOperationsNetOfTaxAttributableToReportingEntity

- **query**: What was GE's Income (Loss) from Discontinued Operations, Net of Tax, Attributable to Parent for the period ended 2023-09-30?
- **as_of**: 2024-04-23   (窗口 364 天, 2 个版本)
- **GOLD**      avail=2023-10-24  GE reported Income (Loss) from Discontinued Operations, Net of Tax, Attributable to Parent of 411,000,000 USD for the period ended 2023-09-30.
- **DISTRACTOR** avail=2024-10-22  GE reported Income (Loss) from Discontinued Operations, Net of Tax, Attributable to Parent of -371,000,000 USD for the period ended 2023-09-30.
- 值差异: 4.11e+08 vs -3.71e+08

## 30. RTX / ContractWithCustomerLiabilityRevenueRecognized

- **query**: What was RTX's Contract with Customer, Liability, Revenue Recognized for the period ended 2021-09-30?
- **as_of**: 2022-04-26   (窗口 364 天, 2 个版本)
- **GOLD**      avail=2021-10-26  RTX reported Contract with Customer, Liability, Revenue Recognized of 960,000,000 USD for the period ended 2021-09-30.
- **DISTRACTOR** avail=2022-10-25  RTX reported Contract with Customer, Liability, Revenue Recognized of 1,000,000,000 USD for the period ended 2021-09-30.
- 值差异: 9.6e+08 vs 1e+09

## 31. TSLA / CurrentFederalTaxExpenseBenefit

- **query**: What was TSLA's Current Federal Tax Expense (Benefit) for the period ended 2017-12-31?
- **as_of**: 2019-02-18   (窗口 720 天, 3 个版本)
- **GOLD**      avail=2018-02-23  TSLA reported Current Federal Tax Expense (Benefit) of -9,552,000 USD for the period ended 2017-12-31.
- **DISTRACTOR** avail=2020-02-13  TSLA reported Current Federal Tax Expense (Benefit) of -10,000,000 USD for the period ended 2017-12-31.
- 值差异: -9.552e+06 vs -1e+07

## 32. ACN / OtherComprehensiveIncomeLossNetOfTaxPortionAttributableToNoncontrollingInterest

- **query**: What was ACN's Other Comprehensive Income (Loss), Net of Tax, Portion Attributable to Noncontrolling Interest for the period ended 2019-08-31?
- **as_of**: 2020-10-21   (窗口 717 天, 3 个版本)
- **GOLD**      avail=2019-10-29  ACN reported Other Comprehensive Income (Loss), Net of Tax, Portion Attributable to Noncontrolling Interest of 6,749,000 USD for the period ended 2019-08-31.
- **DISTRACTOR** avail=2021-10-15  ACN reported Other Comprehensive Income (Loss), Net of Tax, Portion Attributable to Noncontrolling Interest of -6,749,000 USD for the period ended 2019-08-31.
- 值差异: 6.749e+06 vs -6.749e+06

## 33. META / OtherAccruedLiabilitiesCurrent

- **query**: What was META's Other Accrued Liabilities, Current for the period ended 2019-12-31?
- **as_of**: 2020-07-30   (窗口 364 天, 2 个版本)
- **GOLD**      avail=2020-01-30  META reported Other Accrued Liabilities, Current of 2,498,000,000 USD for the period ended 2019-12-31.
- **DISTRACTOR** avail=2021-01-28  META reported Other Accrued Liabilities, Current of 2,327,000,000 USD for the period ended 2019-12-31.
- 值差异: 2.498e+09 vs 2.327e+09

## 34. GE / AvailableForSaleSecuritiesGrossRealizedGainsLossesSaleProceeds

- **query**: What was GE's Available-for-sale Securities, Gross Realized Gains (Losses), Sale Proceeds for the period ended 2014-06-30?
- **as_of**: 2015-01-29   (窗口 364 天, 2 个版本)
- **GOLD**      avail=2014-07-31  GE reported Available-for-sale Securities, Gross Realized Gains (Losses), Sale Proceeds of 2,551,000,000 USD for the period ended 2014-06-30.
- **DISTRACTOR** avail=2015-07-30  GE reported Available-for-sale Securities, Gross Realized Gains (Losses), Sale Proceeds of 1,376,000,000 USD for the period ended 2014-06-30.
- 值差异: 2.551e+09 vs 1.376e+09

## 35. MRK / DeferredTaxLiabilitiesGoodwillAndIntangibleAssetsIntangibleAssets

- **query**: What was MRK's Deferred Tax Liabilities, Intangible Assets for the period ended 2016-12-31?
- **as_of**: 2017-08-29   (窗口 364 天, 2 个版本)
- **GOLD**      avail=2017-02-28  MRK reported Deferred Tax Liabilities, Intangible Assets of 3,734,000,000 USD for the period ended 2016-12-31.
- **DISTRACTOR** avail=2018-02-27  MRK reported Deferred Tax Liabilities, Intangible Assets of 3,854,000,000 USD for the period ended 2016-12-31.
- 值差异: 3.734e+09 vs 3.854e+09

## 36. ADBE / IncreaseDecreaseInAccruedIncomeTaxesPayable

- **query**: What was ADBE's Increase (Decrease) in Income Taxes Payable for the period ended 2016-03-04?
- **as_of**: 2016-09-28   (窗口 364 天, 2 个版本)
- **GOLD**      avail=2016-03-30  ADBE reported Increase (Decrease) in Income Taxes Payable of 2,085,000 USD for the period ended 2016-03-04.
- **DISTRACTOR** avail=2017-03-29  ADBE reported Increase (Decrease) in Income Taxes Payable of 16,940,000 USD for the period ended 2016-03-04.
- 值差异: 2.085e+06 vs 1.694e+07

## 37. RTX / OtherNoncashIncomeExpense

- **query**: What was RTX's Other Noncash Income (Expense) for the period ended 2019-12-31?
- **as_of**: 2020-06-17   (窗口 264 天, 2 个版本)
- **GOLD**      avail=2020-02-06  RTX reported Other Noncash Income (Expense) of 961,000,000 USD for the period ended 2019-12-31.
- **DISTRACTOR** avail=2020-10-27  RTX reported Other Noncash Income (Expense) of -525,000,000 USD for the period ended 2019-12-31.
- 值差异: 9.61e+08 vs -5.25e+08

## 38. MRK / ResearchAndDevelopmentExpense

- **query**: What was MRK's Research and Development Expense for the period ended 2010-06-30?
- **as_of**: 2011-02-05   (窗口 367 天, 2 个版本)
- **GOLD**      avail=2010-08-06  MRK reported Research and Development Expense of 2,150,900,000 USD for the period ended 2010-06-30.
- **DISTRACTOR** avail=2011-08-08  MRK reported Research and Development Expense of 2,179,000,000 USD for the period ended 2010-06-30.
- 值差异: 2.151e+09 vs 2.179e+09

## 39. PFE / NetIncomeLoss

- **query**: What was PFE's Net Income (Loss) Attributable to Parent for the period ended 2020-12-31?
- **as_of**: 2021-08-26   (窗口 364 天, 3 个版本)
- **GOLD**      avail=2021-02-25  PFE reported Net Income (Loss) Attributable to Parent of 9,616,000,000 USD for the period ended 2020-12-31.
- **DISTRACTOR** avail=2022-02-24  PFE reported Net Income (Loss) Attributable to Parent of 9,159,000,000 USD for the period ended 2020-12-31.
- 值差异: 9.616e+09 vs 9.159e+09

## 40. MA / OtherComprehensiveIncomeAvailableForSaleSecuritiesAdjustmentNetOfTaxPeriodIncreaseDecrease

- **query**: What was MA's Other Comprehensive Income (Loss), Available-for-sale Securities Adjustment, Net of Tax for the period ended 2009-06-30?
- **as_of**: 2010-01-31   (窗口 368 天, 2 个版本)
- **GOLD**      avail=2009-07-31  MA reported Other Comprehensive Income (Loss), Available-for-sale Securities Adjustment, Net of Tax of 6,198,000 USD for the period ended 2009-06-30.
- **DISTRACTOR** avail=2010-08-03  MA reported Other Comprehensive Income (Loss), Available-for-sale Securities Adjustment, Net of Tax of 6,000,000 USD for the period ended 2009-06-30.
- 值差异: 6.198e+06 vs 6e+06
