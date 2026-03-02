from facebook_business.adobjects.abstractobject import AbstractObject
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.campaign import Campaign
from facebook_business.api import FacebookAdsApi

access_token = "EAAM53FUCHIgBQ7Jvpd8iXIDPZAVgQscXwiltlFbkb9ixDcRiFoIRlDgH7lk58xv5LGilbaX1Q3xVF7BqrY5mB2uMK04CJtZA4BARutEKu2cb4GffpvxElXuZAZCtXns9S8yZABUvZC2ZCjR4MOqjJLyhlbZBqwSaRxfYpQGeMso3IpJo6zo5iIkPtgZBrqbWzVUbFJEZAu"
app_id = "908043411922056"
ad_account_id = "act_2363271567530123"
campaign_name = "My Quickstart Campaign"

params = {}
FacebookAdsApi.init(access_token=access_token)


# Create an ad campaign with objective OUTCOME_TRAFFIC

fields = []
params = {
    "name": campaign_name,
    "objective": "OUTCOME_TRAFFIC",
    "status": "PAUSED",
    "special_ad_categories": [],
    "is_adset_budget_sharing_enabled": False,
}
campaign = AdAccount(ad_account_id).create_campaign(
    fields=fields,
    params=params,
)
campaign_id = campaign.get_id()

print("Your created campaign id is: " + campaign_id)