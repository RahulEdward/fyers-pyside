# Requirements Document

## Introduction

This document specifies the requirements for a Fyers Auto Trading System - a desktop application built with PySide6 that enables users to manage their trading activities through the Fyers broker. The system provides user authentication, secure broker credential management, and a comprehensive trading dashboard with real-time market data, order management, and portfolio tracking capabilities.

## Glossary

- **System**: The Fyers Auto Trading System application
- **User**: A person who registers and uses the trading application
- **Broker_Credentials**: Fyers API Key and API Secret required for broker authentication
- **Access_Token**: OAuth token obtained from Fyers after successful authentication
- **Request_Token**: Authorization code received from Fyers OAuth flow
- **Dashboard**: Main application interface showing trading features
- **Watchlist**: User-defined list of symbols for price monitoring
- **Order_Book**: List of all orders placed by the user
- **Position**: Current open trading positions held by the user
- **Holdings**: Long-term equity holdings in the user's demat account
- **Funds_Data**: Available margin and balance information
- **WebSocket**: Real-time data streaming connection for live prices
- **SQLite_Database**: Local database for storing user and credential data
- **Encryption_Service**: Service for encrypting/decrypting sensitive data

## Requirements

### Requirement 1: User Registration

**User Story:** As a new user, I want to register with the system, so that I can create an account and access trading features.

#### Acceptance Criteria

1. WHEN a user submits registration with username, password, and email, THE System SHALL validate all fields are non-empty and email format is valid
2. WHEN registration validation passes, THE System SHALL hash the password using a secure algorithm before storage
3. WHEN a user attempts to register with an existing username, THE System SHALL reject the registration and display an error message
4. WHEN registration is successful, THE System SHALL store user data in SQLite_Database and navigate to login screen
5. IF registration fails due to database error, THEN THE System SHALL display an appropriate error message and allow retry

### Requirement 2: User Login

**User Story:** As a registered user, I want to login to the system, so that I can access my trading dashboard.

#### Acceptance Criteria

1. WHEN a user submits login credentials, THE System SHALL validate username and password against stored data
2. WHEN login credentials are valid, THE System SHALL create a session and navigate to broker credentials screen or dashboard
3. WHEN login credentials are invalid, THE System SHALL display an error message and allow retry
4. WHEN a user has existing valid broker credentials, THE System SHALL navigate directly to Dashboard
5. IF database connection fails during login, THEN THE System SHALL display connection error and allow retry

### Requirement 3: Session Management

**User Story:** As a logged-in user, I want my session to be managed securely, so that my account remains protected.

#### Acceptance Criteria

1. WHILE a user is logged in, THE System SHALL maintain session state across application screens
2. WHEN a user clicks logout, THE System SHALL clear session data and navigate to login screen
3. WHEN the application is closed, THE System SHALL clear active session data
4. THE System SHALL store session information securely in memory during active use

### Requirement 4: Broker Credentials Management

**User Story:** As a user, I want to securely store my Fyers broker credentials, so that I can authenticate with the broker.

#### Acceptance Criteria

1. WHEN a user enters Fyers API Key and API Secret, THE System SHALL validate both fields are non-empty
2. WHEN broker credentials are submitted, THE Encryption_Service SHALL encrypt the credentials before storage
3. WHEN encrypted credentials are stored, THE SQLite_Database SHALL associate them with the user account
4. WHEN credentials need to be used, THE Encryption_Service SHALL decrypt them for API authentication
5. IF encryption or storage fails, THEN THE System SHALL display an error and not store plaintext credentials

### Requirement 5: Fyers OAuth Authentication

**User Story:** As a user, I want to authenticate with Fyers using OAuth, so that I can access my trading account.

#### Acceptance Criteria

1. WHEN a user initiates broker authentication, THE System SHALL generate the Fyers OAuth URL with API Key
2. WHEN OAuth URL is generated, THE System SHALL open a browser window for user to login to Fyers
3. WHEN user completes Fyers login, THE System SHALL capture the Request_Token from callback
4. WHEN Request_Token is received, THE System SHALL exchange it for Access_Token using existing auth_api
5. WHEN Access_Token is obtained, THE System SHALL store it securely for API calls
6. IF OAuth flow fails at any step, THEN THE System SHALL display appropriate error and allow retry

### Requirement 6: Dashboard Funds Display

**User Story:** As a user, I want to see my account funds and margin, so that I can know my available trading capital.

#### Acceptance Criteria

1. WHEN Dashboard loads, THE System SHALL fetch Funds_Data using existing funds API
2. WHEN Funds_Data is received, THE System SHALL display available cash, collateral, and utilized margin
3. WHEN Funds_Data is received, THE System SHALL display realized and unrealized P&L
4. IF funds fetch fails, THEN THE System SHALL display error message and provide refresh option

### Requirement 7: Positions Display

**User Story:** As a user, I want to view my open positions, so that I can monitor my current trades.

#### Acceptance Criteria

1. WHEN Dashboard loads or user navigates to positions tab, THE System SHALL fetch positions using existing order_api
2. WHEN positions data is received, THE System SHALL display symbol, quantity, average price, LTP, and P&L
3. WHEN positions data changes, THE System SHALL update the display with new values
4. THE System SHALL provide option to close individual positions or all positions
5. IF positions fetch fails, THEN THE System SHALL display error and provide refresh option

### Requirement 8: Holdings Display

**User Story:** As a user, I want to view my holdings, so that I can see my long-term investments.

#### Acceptance Criteria

1. WHEN user navigates to holdings tab, THE System SHALL fetch holdings using existing order_api
2. WHEN holdings data is received, THE System SHALL display symbol, quantity, average price, current value, and P&L
3. IF holdings fetch fails, THEN THE System SHALL display error and provide refresh option

### Requirement 9: Order Book Display

**User Story:** As a user, I want to view my order history, so that I can track all my placed orders.

#### Acceptance Criteria

1. WHEN user navigates to order book tab, THE System SHALL fetch orders using existing order_api
2. WHEN order data is received, THE System SHALL display order ID, symbol, type, quantity, price, and status
3. WHEN an order is pending, THE System SHALL provide option to cancel or modify it
4. THE System SHALL differentiate between open, completed, and rejected orders visually
5. IF order book fetch fails, THEN THE System SHALL display error and provide refresh option

### Requirement 10: Order Placement

**User Story:** As a user, I want to place trading orders, so that I can execute buy and sell transactions.

#### Acceptance Criteria

1. WHEN user opens order form, THE System SHALL display fields for symbol, exchange, action, quantity, order type, and price
2. WHEN user selects Market order type, THE System SHALL disable price field
3. WHEN user selects Limit or SL order type, THE System SHALL enable and require price field
4. WHEN user submits order, THE System SHALL validate all required fields
5. WHEN order validation passes, THE System SHALL place order using existing order_api
6. WHEN order is placed successfully, THE System SHALL display confirmation with order ID
7. IF order placement fails, THEN THE System SHALL display error message from broker response

### Requirement 11: Order Modification

**User Story:** As a user, I want to modify pending orders, so that I can adjust my trading strategy.

#### Acceptance Criteria

1. WHEN user selects a pending order for modification, THE System SHALL display current order details in editable form
2. WHEN user submits modified order, THE System SHALL validate changed fields
3. WHEN modification is valid, THE System SHALL update order using existing order_api modify function
4. WHEN modification succeeds, THE System SHALL refresh order book display
5. IF modification fails, THEN THE System SHALL display error and retain original order

### Requirement 12: Order Cancellation

**User Story:** As a user, I want to cancel pending orders, so that I can withdraw orders I no longer want.

#### Acceptance Criteria

1. WHEN user requests order cancellation, THE System SHALL confirm the action with user
2. WHEN cancellation is confirmed, THE System SHALL cancel order using existing order_api
3. WHEN cancellation succeeds, THE System SHALL update order status in display
4. IF cancellation fails, THEN THE System SHALL display error message

### Requirement 13: Watchlist Management

**User Story:** As a user, I want to create and manage a watchlist, so that I can monitor specific symbols.

#### Acceptance Criteria

1. WHEN user adds a symbol to watchlist, THE System SHALL validate symbol exists in master contract database
2. WHEN symbol is valid, THE System SHALL add it to user's watchlist in SQLite_Database
3. WHEN watchlist is displayed, THE System SHALL show symbol, LTP, change, and change percentage
4. WHEN user removes a symbol, THE System SHALL delete it from watchlist
5. THE System SHALL persist watchlist across sessions

### Requirement 14: Real-time Price Updates

**User Story:** As a user, I want to see live prices, so that I can make informed trading decisions.

#### Acceptance Criteria

1. WHEN watchlist is displayed, THE System SHALL subscribe to WebSocket for price updates
2. WHEN price update is received via WebSocket, THE System SHALL update the corresponding symbol's display
3. WHEN user navigates away from watchlist, THE System SHALL unsubscribe from WebSocket
4. IF WebSocket connection fails, THEN THE System SHALL attempt reconnection and display connection status
5. WHILE WebSocket is disconnected, THE System SHALL show last known prices with stale indicator

### Requirement 15: Symbol Search

**User Story:** As a user, I want to search for trading symbols, so that I can find instruments to trade or watch.

#### Acceptance Criteria

1. WHEN user enters search text, THE System SHALL query master contract database for matching symbols
2. WHEN search results are found, THE System SHALL display symbol, name, and exchange
3. WHEN user selects a search result, THE System SHALL allow adding to watchlist or opening order form
4. IF no results found, THEN THE System SHALL display appropriate message

### Requirement 16: PySide6 GUI Layout

**User Story:** As a user, I want a clean and modern interface, so that I can use the application efficiently.

#### Acceptance Criteria

1. THE System SHALL display login and registration screens with appropriate input fields and buttons
2. THE System SHALL display Dashboard with tabbed interface for different sections
3. THE System SHALL use consistent styling and Hindi-English labels where appropriate
4. THE System SHALL be responsive to window resizing
5. THE System SHALL display loading indicators during API operations

### Requirement 17: Error Handling and Logging

**User Story:** As a user, I want clear error messages, so that I can understand and resolve issues.

#### Acceptance Criteria

1. WHEN an API error occurs, THE System SHALL display user-friendly error message
2. WHEN a validation error occurs, THE System SHALL highlight the invalid field
3. THE System SHALL log all errors and important events for debugging
4. IF critical error occurs, THEN THE System SHALL allow graceful recovery or restart

### Requirement 18: Data Persistence

**User Story:** As a user, I want my data to persist, so that I don't lose information between sessions.

#### Acceptance Criteria

1. THE SQLite_Database SHALL store user accounts with hashed passwords
2. THE SQLite_Database SHALL store encrypted broker credentials linked to users
3. THE SQLite_Database SHALL store user watchlists
4. WHEN application starts, THE System SHALL initialize database schema if not exists
