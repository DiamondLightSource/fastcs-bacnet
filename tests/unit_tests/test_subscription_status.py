from fastcs_bacnet.practical.BAC0.subscriptions.subscription_id import (
    IPv4SocketAddress,
    ObjectIdentifier,
    SubscriptionID,
)
from fastcs_bacnet.practical.BAC0.subscriptions.subscription_status import (
    Status,
    SubscriptionStatus,
    Team,
    get_oposite_team,
    team_to_status,
)
from fastcs_bacnet.practical.generic.callback_stack import CallbackStack


def test_set_team():
    subscription_id = SubscriptionID(
        IPv4SocketAddress("127.0.0.1", 47808), ObjectIdentifier("analog-output", 0)
    )
    # none of these parameters really matter, just have to fill them in
    status = SubscriptionStatus(CallbackStack(), subscription_id, 60)

    # starting value should be neither
    assert status.get_status() == Status.NEITHER

    status.set_team_up(Team.RED)

    # put one up and it should be up
    assert status.get_status() == Status.RED_UP

    status.set_team_up(Team.BLUE)

    # put the other up and both should be up
    assert status.get_status() == Status.BOTH

    status.set_team_up(Team.BLUE)

    # put one up thats already up shouldnt change anything
    assert status.get_status() == Status.BOTH

    status.set_team_up(Team.RED, False)

    # both up and take one down leaves only the other up
    assert status.get_status() == Status.BLUE_UP

    status.set_team_up(Team.BLUE, False)

    # take down the only one up, both should be down
    assert status.get_status() == Status.NEITHER

    status.set_team_up(Team.RED, False)

    # take one down thats already down nothing should change
    assert status.get_status() == Status.NEITHER


def test_conversions():
    subscription_id = SubscriptionID(
        IPv4SocketAddress("127.0.0.1", 47808), ObjectIdentifier("analog-output", 0)
    )
    # none of these parameters really matter, just have to fill them in
    status = SubscriptionStatus(CallbackStack(), subscription_id, 60)

    # TODO: make a parameter and try both
    try_team = Team.BLUE

    status.set_team_up(try_team)

    # if [team] is put up, status should be [team] (when converted to a team)
    assert status.get_status() == team_to_status(try_team)

    # if you put the oposite team up of the one already up they are both up
    status.set_team_up(get_oposite_team(try_team))
    assert status.get_status() == Status.BOTH


def test_callback_called():
    ### would this be a fixture??
    subscription_id = SubscriptionID(
        IPv4SocketAddress("127.0.0.1", 47808), ObjectIdentifier("analog-output", 0)
    )
    # none of these parameters really matter, just have to fill them in
    status = SubscriptionStatus(CallbackStack(), subscription_id, 60)
    ###

    # by default there is no callback race to prepare for
    assert status.get_callback_called() == Status.NEITHER

    status.set_team_up(Team.BLUE)

    # if only one team is up there will be no race to prepare for
    assert status.get_callback_called() == Status.NEITHER

    status.set_team_up(Team.RED)

    # if both teams are up status should be prepared for a race
    assert status.get_callback_called() == Status.BOTH

    status.set_team_up(Team.BLUE, False)

    # if only one team is up there will be no race to prepare for
    assert status.get_callback_called() == Status.NEITHER
