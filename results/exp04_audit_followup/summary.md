# Exp04 post-hoc checks after the pre-submission audit

All post hoc. Points; delete-one-root jackknife 95% CIs.

| sample   | check                                     | term          |   estimate |   ci_lo |   ci_hi |   pairs |
|:---------|:------------------------------------------|:--------------|-----------:|--------:|--------:|--------:|
| primary  | pre-specified model                       | same_root     |      13.29 |   10.78 |   15.8  |  173755 |
| primary  | without the two largest roots             | same_root     |      15.95 |   12.79 |   19.11 |  131841 |
| primary  | controlling for same uploader             | same_root     |      12.93 |   10.8  |   15.07 |  173755 |
| primary  | controlling for same uploader             | same_uploader |       6.75 |    3.97 |    9.53 |  173755 |
| primary  | excluding same-root pairs by one uploader | same_root     |      12.3  |   10.5  |   14.09 |  173615 |
| expanded | pre-specified model                       | same_root     |      12.74 |   10.98 |   14.51 |  430128 |
| expanded | without the two largest roots             | same_root     |      13.79 |   11.61 |   15.96 |  359976 |
| expanded | controlling for same uploader             | same_root     |      12.3  |   10.65 |   13.94 |  430128 |
| expanded | controlling for same uploader             | same_uploader |       5.33 |    3.14 |    7.51 |  430128 |
| expanded | excluding same-root pairs by one uploader | same_root     |      11.95 |   10.34 |   13.56 |  429672 |

Jackknife variance of the shared-root coefficient due to the most influential root deletions (share of the sum of squared deviations):

- primary: top 1 68.6%, top 5 86.4%, top 10 92.9%; leave-one-root-out range 13.10 to 14.36
- expanded: top 1 37.8%, top 5 77.2%, top 10 89.3%; leave-one-root-out range 12.52 to 13.30
