| step                                          |    rows |
|:----------------------------------------------|--------:|
| Raw rows in orders table                      | 5961005 |
| Outside FY window (2025-04-01 onward)         |  -17115 |
| FY orders                                     | 5943890 |
| Excluded branches (-1, 3, 11)                 |    -438 |
| Not paid (cancel / pending / rejected / NULL) | -508357 |
| Clean paid sales orders                       | 5435095 |
| Of which zero/negative total (flagged, kept)  |   96199 |