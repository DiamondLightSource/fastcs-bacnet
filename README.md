[![CI](https://github.com/DiamondLightSource/fastcs-bacnet/actions/workflows/ci.yml/badge.svg)](https://github.com/DiamondLightSource/fastcs-bacnet/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/DiamondLightSource/fastcs-bacnet/branch/main/graph/badge.svg)](https://codecov.io/gh/DiamondLightSource/fastcs-bacnet)
[![PyPI](https://img.shields.io/pypi/v/fastcs-bacnet.svg)](https://pypi.org/project/fastcs-bacnet)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)

# Dual Subscription Single Callback Branch

This is a branch no longer being developed. However, it may be useful in the future. Most of its new content can be found in src/fastcs_bacnet/practical/BAC0/subscriptions.

Its original intention was to run 2 subscriptions simultaneously to ensure no updates were dropped. At the same time it would make sure that the callback function(s) were only called once.

## Keeping 2 subscriptions alive simultaneously

The individual subscription requests are reffered to as CoVs whilst the pair of them together was called the subscription. They were also put into "teams", named red and blue. One CoV would be sent out with a lifetime (usually 2 hours), half way through this lifetime another CoV would be sent out with the same lifetime. Then, when one ran out the other should still be halfway through its lifetime. The other scenario this is useful for is when a subscription fails to automatically resubscribe. Say the red subscription fails to resubscribe, the blue subscription would still have half its lifetime of being up. Then when the blue subscription comes to automatically resubscribe two things can happen. If it suceeds then we know the red subscription should have worked and we can try it again in half a lifetime. If it failed then we can assume the device has been turned off or disconnected  as two CoV requests have failed consecutively.

## Running the callback function(s) once

Since we have two subscriptions running simultaneously the callback functions should be called when both of them recieve an update. However, this is not what we want. To get around this a race is set up. Both CoVs have access to an object with a lock and a status variable. Both teams try to access this lock when they recieve an update. The first team to lock the other out then sets the status variable to their team (red or blue), calls the callbacks and finally unlocks the object. The other team then accesses the object, checks the status, sees the other team has already called the callback and resets the object for the next race.


## More Problems
A couple extra problems to think about:
What if another race starts before the second has finished?
BAC0 CoVs automatically restart 2 seconds before the last ends, this means there is a 2 second period when 2 CoVs from the same team exist. Races and callbacks must be protected against this factor OR previous CoV must be cancelled when the new one is sent out.
What to do when one CoV recieves an update and the other doesnt AND how to detect this
