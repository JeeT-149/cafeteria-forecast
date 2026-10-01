| step                                          |    rows |
|:----------------------------------------------|--------:|
| Raw rows in orders table                      | 5961005 |
| Outside FY window                             |  -17115 |
| FY orders                                     | 5943890 |
| Excluded branches (-1, 3, 11)                 |    -438 |
| Not paid (cancel / pending / rejected / NULL) | -508357 |
| Clean paid sales orders                       | 5435095 |
| Flagged: non-positive total                   |   96199 |
| Forecast-valid paid orders                    | 5338896 |
| Flagged: repeated invoice number              |   12848 |
| Flagged: repeated business key                |    4084 |
| Flagged: bulk order (> 10,000)                |      67 |