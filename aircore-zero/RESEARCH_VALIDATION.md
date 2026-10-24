# AirCore Zero: validation plan

## Claim under test
After a transmitter is switched off at time zero, a reader can recover a previously selected arbitrary message exactly, bit by bit, after 365 days, with no conventional storage device and no other retained copy.

## Required definitions before testing
1. State what counts as conventional storage and what physical state is hypothesized to retain information.
2. Specify message length, message-generation procedure, reader hardware, environmental conditions, decoding algorithm, and success threshold.
3. Publish the protocol and analysis plan before collecting outcomes.

## Minimum protocol
- Generate cryptographically random messages after the apparatus and reader have been inspected.
- Keep the message-generation key and ground truth inaccessible to the reader operator.
- Disconnect transmitter power and verify no wired/wireless/network path can retain or relay the message.
- Use blinded negative controls containing different random messages and sham apparatus.
- Record environmental and instrument data continuously, with tamper-evident logs.
- At the preregistered time, decode once using the locked procedure and compare every bit with ground truth.
- Repeat with independent apparatus and operators; report all failures and exclusions.

## Interpretation
A successful software simulation demonstrates only that the software behaves as specified on simulated inputs. It does not demonstrate year-long physical persistence. A positive physical result requires independent replication and exclusion of ordinary storage, leakage, contamination, and measurement artifacts.

## Current status
No year-long physical test has been completed. The physical mechanism and supporting evidence remain unverified.
