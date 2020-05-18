Feature: Financial Report Feature

  Scenario: GET "/api/reports/financial" by anonymous user
    Given an anonymous user
    When I request GET "/api/reports/financial" with parameters interval_from, interval_to
    Then I should get 401 Unauthorized

  Scenario: GET "/api/reports/financial" with parameters interval_from, interval_to by authorized user
    Given an authorized user
    And several groups
    And several users
    And several advertisers
    And several campaigns
    And several financial reports
    When I request GET "/api/reports/financial" with parameters interval_from, interval_to
    Then I should get financial report

  Scenario: GET "/api/reports/financial" with parameters interval_from, interval_to, campaign_id by authorized user
    Given an authorized user
    And several groups
    And several users
    And several advertisers
    And several campaigns
    And several financial reports
    When I request GET "/api/reports/financial" with parameters interval_from, interval_to, campaign_id
    Then I should get campaign financial report

  Scenario: POST "/api/reports/financial" by anonymous user
    Given an anonymous user
    When I request POST "/api/reports/financial" by anonymous user
    Then I should get 401 Unauthorized

  Scenario: POST "/api/reports/financial" by authorized user
    Given an authorized user
    And several groups
    And several users
    And several advertisers
    And several campaigns
    And several financial reports
    When I request POST "/api/reports/financial"
    Then I should get created campaign financial report

  Scenario: PATCH "/api/reports/financial" by anonymous user
    Given an anonymous user
    When I request PATCH "/api/reports/financial" by anonymous user
    Then I should get 401 Unauthorized

  Scenario: PATCH "/api/reports/financial" by authorized user
    Given an authorized user
    And several groups
    And several users
    And several advertisers
    And several campaigns
    And several financial reports
    When I request PATCH "/api/reports/financial"
    Then I should get updated campaign financial report
