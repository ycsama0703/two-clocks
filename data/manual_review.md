# Phase-0 项(1) 人工核查样本（40 对，v2 语料，随机种子 11）

avail_time = max(filingDate, acceptanceDate)。检查：(a) 两候选是否同一 (公司,科目,报告期)；
(b) as_of 下 gold 已披露、distractor 未披露；(c) 文本有无可推断披露时间的线索。

## 1. HBM / ChangesInEquity

- **query**: What was HBM's changes in equity for the period ended 2019-12-31?
- **as_of**: 2020-09-29  (窗口 364 天, 2 版本)
- **GOLD**       avail=2020-03-31  HBM reported changes in equity of -3,927,000 USD for the period ended 2019-12-31.
- **DISTRACTOR**  avail=2021-03-30  HBM reported changes in equity of 3,927,000 USD for the period ended 2019-12-31.

## 2. ABT / GainLossOnContractTermination

- **query**: What was ABT's Gain (Loss) on Contract Termination for the period ended 2012-06-30?
- **as_of**: 2013-02-05  (窗口 364 天, 2 版本)
- **GOLD**       avail=2012-08-07  ABT reported Gain (Loss) on Contract Termination of 60,000,000 USD for the period ended 2012-06-30.
- **DISTRACTOR**  avail=2013-08-06  ABT reported Gain (Loss) on Contract Termination of 40,000,000 USD for the period ended 2012-06-30.

## 3. JNJ / IncreaseDecreaseInInventories

- **query**: What was JNJ's Increase (Decrease) in Inventories for the period ended 2009-09-27?
- **as_of**: 2010-05-08  (窗口 371 天, 2 版本)
- **GOLD**       avail=2009-11-04  JNJ reported Increase (Decrease) in Inventories of -250,000,000 USD for the period ended 2009-09-27.
- **DISTRACTOR**  avail=2010-11-10  JNJ reported Increase (Decrease) in Inventories of 250,000,000 USD for the period ended 2009-09-27.

## 4. LLY / OtherComprehensiveIncomeUnrealizedGainLossOnDerivativesArisingDuringPeriodTax

- **query**: What was LLY's Other Comprehensive Income (Loss), Unrealized Gain (Loss) on Derivatives Arising During Period, Tax for the period ended 2014-09-30?
- **as_of**: 2015-04-30  (窗口 366 天, 2 版本)
- **GOLD**       avail=2014-10-29  LLY reported Other Comprehensive Income (Loss), Unrealized Gain (Loss) on Derivatives Arising During Period, Tax of 19,900,000 USD for the period ended 2014-09-30.
- **DISTRACTOR**  avail=2015-10-30  LLY reported Other Comprehensive Income (Loss), Unrealized Gain (Loss) on Derivatives Arising During Period, Tax of -19,900,000 USD for the period ended 2014-09-30.

## 5. MRK / ResearchAndDevelopmentExpense

- **query**: What was MRK's Research and Development Expense for the period ended 2020-12-31?
- **as_of**: 2021-08-26  (窗口 365 天, 3 版本)
- **GOLD**       avail=2021-02-25  MRK reported Research and Development Expense of 13,558,000,000 USD for the period ended 2020-12-31.
- **DISTRACTOR**  avail=2022-02-25  MRK reported Research and Development Expense of 13,397,000,000 USD for the period ended 2020-12-31.

## 6. HL / OtherNoncashExpense

- **query**: What was HL's Other Noncash Expense for the period ended 2013-12-31?
- **as_of**: 2014-08-20  (窗口 364 天, 3 版本)
- **GOLD**       avail=2014-02-19  HL reported Other Noncash Expense of -841,000 USD for the period ended 2013-12-31.
- **DISTRACTOR**  avail=2015-02-18  HL reported Other Noncash Expense of 86,000 USD for the period ended 2013-12-31.

## 7. WFC / OtherComprehensiveIncomeLossFinancialLiabilityFairValueOptionUnrealizedGainLossArisingDuringPeriodAfterTax

- **query**: What was WFC's Other Comprehensive Income (Loss), Financial Liability, Fair Value Option, Unrealized Gain (Loss) Arising During Period, after Tax for the period ended 2022-06-30?
- **as_of**: 2023-01-30  (窗口 365 天, 2 版本)
- **GOLD**       avail=2022-08-01  WFC reported Other Comprehensive Income (Loss), Financial Liability, Fair Value Option, Unrealized Gain (Loss) Arising During Period, after Tax of 4,000,000 USD for the period ended 2022-06-30.
- **DISTRACTOR**  avail=2023-08-01  WFC reported Other Comprehensive Income (Loss), Financial Liability, Fair Value Option, Unrealized Gain (Loss) Arising During Period, after Tax of 89,000,000 USD for the period ended 2022-06-30.

## 8. RTX / UnrecognizedTaxBenefitsInterestOnIncomeTaxesExpense

- **query**: What was RTX's Unrecognized Tax Benefits, Interest on Income Taxes Expense for the period ended 2020-09-30?
- **as_of**: 2021-04-27  (窗口 364 天, 2 版本)
- **GOLD**       avail=2020-10-27  RTX reported Unrecognized Tax Benefits, Interest on Income Taxes Expense of 11,000,000 USD for the period ended 2020-09-30.
- **DISTRACTOR**  avail=2021-10-26  RTX reported Unrecognized Tax Benefits, Interest on Income Taxes Expense of 33,000,000 USD for the period ended 2020-09-30.

## 9. CSCO / FinancingReceivableAllowanceForCreditLossForeignCurrencyTranslation

- **query**: What was CSCO's Financing Receivable, Allowance for Credit Loss, Foreign Currency Translation for the period ended 2025-04-26?
- **as_of**: 2025-11-18  (窗口 364 天, 2 版本)
- **GOLD**       avail=2025-05-20  CSCO reported Financing Receivable, Allowance for Credit Loss, Foreign Currency Translation of 4,000,000 USD for the period ended 2025-04-26.
- **DISTRACTOR**  avail=2026-05-19  CSCO reported Financing Receivable, Allowance for Credit Loss, Foreign Currency Translation of -4,000,000 USD for the period ended 2025-04-26.

## 10. SPXC / AmortizationOfIntangibleAssets

- **query**: What was SPXC's Amortization of Intangible Assets for the period ended 2011-10-01?
- **as_of**: 2012-05-02  (窗口 364 天, 2 版本)
- **GOLD**       avail=2011-11-02  SPXC reported Amortization of Intangible Assets of 24,800,000 USD for the period ended 2011-10-01.
- **DISTRACTOR**  avail=2012-10-31  SPXC reported Amortization of Intangible Assets of 16,900,000 USD for the period ended 2011-10-01.

## 11. UNP / IncomeTaxesPaidNet

- **query**: What was UNP's Income Taxes Paid, Net for the period ended 2013-09-30?
- **as_of**: 2014-04-20  (窗口 371 天, 2 版本)
- **GOLD**       avail=2013-10-17  UNP reported Income Taxes Paid, Net of -1,165,000,000 USD for the period ended 2013-09-30.
- **DISTRACTOR**  avail=2014-10-23  UNP reported Income Taxes Paid, Net of 1,165,000,000 USD for the period ended 2013-09-30.

## 12. DHR / ComprehensiveIncomeNetOfTax

- **query**: What was DHR's Comprehensive Income (Loss), Net of Tax, Attributable to Parent for the period ended 2011-09-30?
- **as_of**: 2012-04-19  (窗口 364 天, 2 版本)
- **GOLD**       avail=2011-10-20  DHR reported Comprehensive Income (Loss), Net of Tax, Attributable to Parent of -29,300,000 USD for the period ended 2011-09-30.
- **DISTRACTOR**  avail=2012-10-18  DHR reported Comprehensive Income (Loss), Net of Tax, Attributable to Parent of -24,439,000 USD for the period ended 2011-09-30.

## 13. SPXC / EffectiveIncomeTaxRateReconciliationNondeductibleExpense

- **query**: What was SPXC's Effective Income Tax Rate Reconciliation, Nondeductible Expense, Percent for the period ended 2020-12-31?
- **as_of**: 2021-08-27  (窗口 364 天, 3 版本)
- **GOLD**       avail=2021-02-26  SPXC reported Effective Income Tax Rate Reconciliation, Nondeductible Expense, Percent of 0.015 for the period ended 2020-12-31.
- **DISTRACTOR**  avail=2022-02-25  SPXC reported Effective Income Tax Rate Reconciliation, Nondeductible Expense, Percent of 0.022 for the period ended 2020-12-31.

## 14. WMT / IncreaseDecreaseInRetailRelatedInventories

- **query**: What was WMT's Increase (Decrease) in Retail Related Inventories for the period ended 2010-04-30?
- **as_of**: 2010-12-03  (窗口 364 天, 2 版本)
- **GOLD**       avail=2010-06-04  WMT reported Increase (Decrease) in Retail Related Inventories of 2,230,000,000 USD for the period ended 2010-04-30.
- **DISTRACTOR**  avail=2011-06-03  WMT reported Increase (Decrease) in Retail Related Inventories of 2,195,000,000 USD for the period ended 2010-04-30.

## 15. HON / DeferredFederalIncomeTaxExpenseBenefit

- **query**: What was HON's Deferred Federal Income Tax Expense (Benefit) for the period ended 2017-12-31?
- **as_of**: 2018-08-10  (窗口 364 天, 3 版本)
- **GOLD**       avail=2018-02-09  HON reported Deferred Federal Income Tax Expense (Benefit) of 39,000,000 USD for the period ended 2017-12-31.
- **DISTRACTOR**  avail=2019-02-08  HON reported Deferred Federal Income Tax Expense (Benefit) of 190,000,000 USD for the period ended 2017-12-31.

## 16. GE / OtherThanTemporaryImpairmentCreditLossesRecognizedInEarningsAdditionsAdditionalCreditLosses

- **query**: What was GE's Other than Temporary Impairment, Credit Losses Recognized in Earnings, Additions, Additional Credit Losses for the period ended 2014-09-30?
- **as_of**: 2015-05-04  (窗口 363 天, 2 版本)
- **GOLD**       avail=2014-11-04  GE reported Other than Temporary Impairment, Credit Losses Recognized in Earnings, Additions, Additional Credit Losses of 34,000,000 USD for the period ended 2014-09-30.
- **DISTRACTOR**  avail=2015-11-02  GE reported Other than Temporary Impairment, Credit Losses Recognized in Earnings, Additions, Additional Credit Losses of 4,000,000 USD for the period ended 2014-09-30.

## 17. SPXC / OperatingIncomeLoss

- **query**: What was SPXC's Operating Income (Loss) for the period ended 2017-07-01?
- **as_of**: 2018-02-02  (窗口 364 天, 2 版本)
- **GOLD**       avail=2017-08-04  SPXC reported Operating Income (Loss) of 21,900,000 USD for the period ended 2017-07-01.
- **DISTRACTOR**  avail=2018-08-03  SPXC reported Operating Income (Loss) of 24,300,000 USD for the period ended 2017-07-01.

## 18. PFE / NetIncomeLossAvailableToCommonStockholdersBasic

- **query**: What was PFE's Net Income (Loss) Available to Common Stockholders, Basic for the period ended 2020-09-27?
- **as_of**: 2021-05-10  (窗口 372 天, 2 版本)
- **GOLD**       avail=2020-11-05  PFE reported Net Income (Loss) Available to Common Stockholders, Basic of 9,021,000,000 USD for the period ended 2020-09-27.
- **DISTRACTOR**  avail=2021-11-12  PFE reported Net Income (Loss) Available to Common Stockholders, Basic of 8,313,000,000 USD for the period ended 2020-09-27.

## 19. ACN / NetCashProvidedByUsedInOperatingActivities

- **query**: What was ACN's Net Cash Provided by (Used in) Operating Activities for the period ended 2016-02-29?
- **as_of**: 2016-09-22  (窗口 364 天, 2 版本)
- **GOLD**       avail=2016-03-24  ACN reported Net Cash Provided by (Used in) Operating Activities of 928,651,000 USD for the period ended 2016-02-29.
- **DISTRACTOR**  avail=2017-03-23  ACN reported Net Cash Provided by (Used in) Operating Activities of 1,007,452,000 USD for the period ended 2016-02-29.

## 20. NEE / ProceedsFromPaymentsForOtherFinancingActivities

- **query**: What was NEE's Proceeds from (Payments for) Other Financing Activities for the period ended 2009-12-31?
- **as_of**: 2010-08-28  (窗口 367 天, 2 版本)
- **GOLD**       avail=2010-02-26  NEE reported Proceeds from (Payments for) Other Financing Activities of -1,000,000 USD for the period ended 2009-12-31.
- **DISTRACTOR**  avail=2011-02-28  NEE reported Proceeds from (Payments for) Other Financing Activities of 4,000,000 USD for the period ended 2009-12-31.

## 21. ZION / FeesAndCommissionsOther

- **query**: What was ZION's Fees and Commissions, Other for the period ended 2014-06-30?
- **as_of**: 2015-02-05  (窗口 364 天, 2 版本)
- **GOLD**       avail=2014-08-07  ZION reported Fees and Commissions, Other of 91,032,000 USD for the period ended 2014-06-30.
- **DISTRACTOR**  avail=2015-08-06  ZION reported Fees and Commissions, Other of 92,208,000 USD for the period ended 2014-06-30.

## 22. PEP / DepreciationAndAmortization

- **query**: What was PEP's Depreciation, Depletion and Amortization, Nonproduction for the period ended 2025-03-22?
- **as_of**: 2025-10-19  (窗口 357 天, 2 版本)
- **GOLD**       avail=2025-04-24  PEP reported Depreciation, Depletion and Amortization, Nonproduction of 669,000,000 USD for the period ended 2025-03-22.
- **DISTRACTOR**  avail=2026-04-16  PEP reported Depreciation, Depletion and Amortization, Nonproduction of 684,000,000 USD for the period ended 2025-03-22.

## 23. SPXC / NoncurrentAssets

- **query**: What was SPXC's Long-Lived Assets for the period ended 2020-12-31?
- **as_of**: 2021-08-27  (窗口 364 天, 3 版本)
- **GOLD**       avail=2021-02-26  SPXC reported Long-Lived Assets of 810,200,000 USD for the period ended 2020-12-31.
- **DISTRACTOR**  avail=2022-02-25  SPXC reported Long-Lived Assets of 831,500,000 USD for the period ended 2020-12-31.

## 24. WFC / OtherNoninterestExpense

- **query**: What was WFC's Other Noninterest Expense for the period ended 2022-12-31?
- **as_of**: 2023-08-22  (窗口 364 天, 3 版本)
- **GOLD**       avail=2023-02-21  WFC reported Other Noninterest Expense of 4,004,000,000 USD for the period ended 2022-12-31.
- **DISTRACTOR**  avail=2024-02-20  WFC reported Other Noninterest Expense of 3,932,000,000 USD for the period ended 2022-12-31.

## 25. GE / CostsAndExpenses

- **query**: What was GE's Costs and Expenses for the period ended 2010-09-30?
- **as_of**: 2011-05-07  (窗口 370 天, 2 版本)
- **GOLD**       avail=2010-11-03  GE reported Costs and Expenses of 9,146,000,000 USD for the period ended 2010-09-30.
- **DISTRACTOR**  avail=2011-11-08  GE reported Costs and Expenses of 31,790,000,000 USD for the period ended 2010-09-30.

## 26. SPXC / ProductWarrantyAccrualWarrantiesIssued

- **query**: What was SPXC's Standard and Extended Product Warranty Accrual, Increase for Warranties Issued for the period ended 2014-12-31?
- **as_of**: 2015-08-26  (窗口 368 天, 3 版本)
- **GOLD**       avail=2015-02-23  SPXC reported Standard and Extended Product Warranty Accrual, Increase for Warranties Issued of 34,900,000 USD for the period ended 2014-12-31.
- **DISTRACTOR**  avail=2016-02-26  SPXC reported Standard and Extended Product Warranty Accrual, Increase for Warranties Issued of 21,400,000 USD for the period ended 2014-12-31.

## 27. GE / ProvisionForLoanAndLeaseLosses

- **query**: What was GE's Provision for Loan and Lease Losses for the period ended 2014-09-30?
- **as_of**: 2015-05-04  (窗口 363 天, 2 版本)
- **GOLD**       avail=2014-11-04  GE reported Provision for Loan and Lease Losses of 957,000,000 USD for the period ended 2014-09-30.
- **DISTRACTOR**  avail=2015-11-02  GE reported Provision for Loan and Lease Losses of 858,000,000 USD for the period ended 2014-09-30.

## 28. ZION / DerivativeInstrumentsGainLossRecognizedInOtherComprehensiveIncomeEffectivePortionNet

- **query**: What was ZION's Derivative Instruments, Gain (Loss) Recognized in Other Comprehensive Income (Loss), Effective Portion, Net for the period ended 2016-09-30?
- **as_of**: 2017-05-09  (窗口 366 天, 2 版本)
- **GOLD**       avail=2016-11-07  ZION reported Derivative Instruments, Gain (Loss) Recognized in Other Comprehensive Income (Loss), Effective Portion, Net of -5,381,000 USD for the period ended 2016-09-30.
- **DISTRACTOR**  avail=2017-11-08  ZION reported Derivative Instruments, Gain (Loss) Recognized in Other Comprehensive Income (Loss), Effective Portion, Net of -5,000,000 USD for the period ended 2016-09-30.

## 29. SPXC / PaymentsForRestructuring

- **query**: What was SPXC's Payments for Restructuring for the period ended 2012-12-31?
- **as_of**: 2013-08-23  (窗口 364 天, 3 版本)
- **GOLD**       avail=2013-02-22  SPXC reported Payments for Restructuring of 20,100,000 USD for the period ended 2012-12-31.
- **DISTRACTOR**  avail=2014-02-21  SPXC reported Payments for Restructuring of 19,100,000 USD for the period ended 2012-12-31.

## 30. ZION / NetCashProvidedByUsedInOperatingActivities

- **query**: What was ZION's Net Cash Provided by (Used in) Operating Activities for the period ended 2014-06-30?
- **as_of**: 2015-02-05  (窗口 364 天, 2 版本)
- **GOLD**       avail=2014-08-07  ZION reported Net Cash Provided by (Used in) Operating Activities of 12,426,000 USD for the period ended 2014-06-30.
- **DISTRACTOR**  avail=2015-08-06  ZION reported Net Cash Provided by (Used in) Operating Activities of 13,393,000 USD for the period ended 2014-06-30.

## 31. GS / FairValueNetDerivativeAssetLiabilityMeasuredOnRecurringBasisUnobservableInputsReconciliationSales

- **query**: What was GS's Fair Value, Net Derivative Asset (Liability) Measured on Recurring Basis, Unobservable Inputs Reconciliation, Sales for the period ended 2022-03-31?
- **as_of**: 2022-11-01  (窗口 367 天, 2 版本)
- **GOLD**       avail=2022-05-02  GS reported Fair Value, Net Derivative Asset (Liability) Measured on Recurring Basis, Unobservable Inputs Reconciliation, Sales of -1,025,000,000 USD for the period ended 2022-03-31.
- **DISTRACTOR**  avail=2023-05-04  GS reported Fair Value, Net Derivative Asset (Liability) Measured on Recurring Basis, Unobservable Inputs Reconciliation, Sales of 1,025,000,000 USD for the period ended 2022-03-31.

## 32. SPXC / OperatingIncomeLoss

- **query**: What was SPXC's Operating Income (Loss) for the period ended 2012-09-29?
- **as_of**: 2013-05-01  (窗口 364 天, 2 版本)
- **GOLD**       avail=2012-10-31  SPXC reported Operating Income (Loss) of 85,900,000 USD for the period ended 2012-09-29.
- **DISTRACTOR**  avail=2013-10-30  SPXC reported Operating Income (Loss) of 76,600,000 USD for the period ended 2012-09-29.

## 33. GOOGL / OtherComprehensiveIncomeLossDerivativesQualifyingAsHedgesTax

- **query**: What was GOOGL's Other Comprehensive Income (Loss), Derivatives Qualifying as Hedges, Tax for the period ended 2015-09-30?
- **as_of**: 2016-05-01  (窗口 371 天, 2 版本)
- **GOLD**       avail=2015-10-29  GOOGL reported Other Comprehensive Income (Loss), Derivatives Qualifying as Hedges, Tax of -58,000,000 USD for the period ended 2015-09-30.
- **DISTRACTOR**  avail=2016-11-03  GOOGL reported Other Comprehensive Income (Loss), Derivatives Qualifying as Hedges, Tax of 58,000,000 USD for the period ended 2015-09-30.

## 34. SPXC / BusinessAcquisitionProFormaEarningsPerShareBasic

- **query**: What was SPXC's Business Acquisition, Pro Forma Earnings Per Share, Basic for the period ended 2024-06-29?
- **as_of**: 2025-01-31  (窗口 364 天, 2 版本)
- **GOLD**       avail=2024-08-02  SPXC reported Business Acquisition, Pro Forma Earnings Per Share, Basic of 2.13 USD per share for the period ended 2024-06-29.
- **DISTRACTOR**  avail=2025-08-01  SPXC reported Business Acquisition, Pro Forma Earnings Per Share, Basic of 1.65 USD per share for the period ended 2024-06-29.

## 35. WFC / OtherComprehensiveIncomeLossNetOfTax

- **query**: What was WFC's Other Comprehensive Income (Loss), Net of Tax for the period ended 2017-09-30?
- **as_of**: 2018-05-06  (窗口 368 天, 2 版本)
- **GOLD**       avail=2017-11-03  WFC reported Other Comprehensive Income (Loss), Net of Tax of 449,000,000 USD for the period ended 2017-09-30.
- **DISTRACTOR**  avail=2018-11-06  WFC reported Other Comprehensive Income (Loss), Net of Tax of 492,000,000 USD for the period ended 2017-09-30.

## 36. UNP / WeightedAverageNumberOfSharesOutstandingBasic

- **query**: What was UNP's Weighted Average Number of Shares Outstanding, Basic for the period ended 2014-03-31?
- **as_of**: 2014-10-19  (窗口 371 天, 2 版本)
- **GOLD**       avail=2014-04-17  UNP reported Weighted Average Number of Shares Outstanding, Basic of 454,100,000 shares for the period ended 2014-03-31.
- **DISTRACTOR**  avail=2015-04-23  UNP reported Weighted Average Number of Shares Outstanding, Basic of 908,100,000 shares for the period ended 2014-03-31.

## 37. DHR / IncreaseDecreaseInAccountsReceivable

- **query**: What was DHR's Increase (Decrease) in Accounts Receivable for the period ended 2015-04-03?
- **as_of**: 2015-10-22  (窗口 364 天, 2 版本)
- **GOLD**       avail=2015-04-23  DHR reported Increase (Decrease) in Accounts Receivable of -125,600,000 USD for the period ended 2015-04-03.
- **DISTRACTOR**  avail=2016-04-21  DHR reported Increase (Decrease) in Accounts Receivable of -104,200,000 USD for the period ended 2015-04-03.

## 38. HL / ComprehensiveIncomeNetOfTax

- **query**: What was HL's Comprehensive Income (Loss), Net of Tax, Attributable to Parent for the period ended 2017-09-30?
- **as_of**: 2018-05-09  (窗口 367 天, 2 版本)
- **GOLD**       avail=2017-11-07  HL reported Comprehensive Income (Loss), Net of Tax, Attributable to Parent of 17,948,000 USD for the period ended 2017-09-30.
- **DISTRACTOR**  avail=2018-11-09  HL reported Comprehensive Income (Loss), Net of Tax, Attributable to Parent of 14,165,000 USD for the period ended 2017-09-30.

## 39. ZION / AllowanceForLoanAndLeaseLossesWriteOffs

- **query**: What was ZION's Allowance for Loan and Lease Losses, Write-offs for the period ended 2018-09-30?
- **as_of**: 2019-05-07  (窗口 363 天, 2 版本)
- **GOLD**       avail=2018-11-07  ZION reported Allowance for Loan and Lease Losses, Write-offs of -56,000,000 USD for the period ended 2018-09-30.
- **DISTRACTOR**  avail=2019-11-05  ZION reported Allowance for Loan and Lease Losses, Write-offs of 56,000,000 USD for the period ended 2018-09-30.

## 40. MRK / EffectiveIncomeTaxRateReconciliationTaxCreditsResearch

- **query**: What was MRK's Effective Income Tax Rate Reconciliation, Tax Credit, Research, Percent for the period ended 2020-12-31?
- **as_of**: 2021-08-26  (窗口 365 天, 3 版本)
- **GOLD**       avail=2021-02-25  MRK reported Effective Income Tax Rate Reconciliation, Tax Credit, Research, Percent of 0.013 for the period ended 2020-12-31.
- **DISTRACTOR**  avail=2022-02-25  MRK reported Effective Income Tax Rate Reconciliation, Tax Credit, Research, Percent of 0.018 for the period ended 2020-12-31.
