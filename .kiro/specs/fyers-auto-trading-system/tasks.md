# Implementation Plan: Fyers Auto Trading System

## Overview

This implementation plan breaks down the Fyers Auto Trading System into discrete coding tasks. The system is built with PySide6 for GUI, SQLite for local storage, and integrates with existing Fyers API code. Tasks are organized to build incrementally, with each task building on previous work.

## Tasks

- [x] 1. Project Setup and Database Layer
  - [x] 1.1 Create project structure and install dependencies
    - Create directory structure: `src/`, `src/models/`, `src/services/`, `src/repositories/`, `src/ui/`, `src/ui/windows/`, `src/ui/widgets/`, `tests/`
    - Create `requirements.txt` with PySide6, SQLAlchemy, cryptography, bcrypt, hypothesis
    - Create `src/__init__.py` and package init files
    - _Requirements: 18.4_

  - [x] 1.2 Implement data models
    - Create `src/models/user.py` with User, Session dataclasses
    - Create `src/models/credentials.py` with BrokerCredentials, EncryptedCredentials dataclasses
    - Create `src/models/trading.py` with FundsData, Position, Holding, Order, OrderRequest, OrderModification dataclasses
    - Create `src/models/watchlist.py` with WatchlistItem, QuoteData, SymbolInfo dataclasses
    - Create `src/models/enums.py` with OrderType, OrderAction, OrderStatus, ProductType enums
    - Create `src/models/result.py` with Result type (Ok, Err)
    - _Requirements: Data Models from Design_

  - [x] 1.3 Implement database schema and initialization
    - Create `src/database/schema.py` with SQLAlchemy models for users, broker_credentials, watchlist tables
    - Create `src/database/connection.py` with database connection management
    - Implement `init_db()` function to create tables if not exist
    - _Requirements: 18.4_

  - [x] 1.4 Implement UserRepository
    - Create `src/repositories/user_repository.py`
    - Implement `create()`, `find_by_username()`, `find_by_id()`, `exists()` methods
    - _Requirements: 1.4, 2.1_

  - [ ]* 1.5 Write property test for username uniqueness
    - **Property 3: Username Uniqueness**
    - **Validates: Requirements 1.3**

  - [x] 1.6 Implement CredentialRepository
    - Create `src/repositories/credential_repository.py`
    - Implement `save()`, `get()`, `exists()`, `update_access_token()` methods
    - _Requirements: 4.3, 18.2_

  - [x] 1.7 Implement WatchlistRepository
    - Create `src/repositories/watchlist_repository.py`
    - Implement `add()`, `remove()`, `get_all()`, `exists()` methods
    - _Requirements: 13.2, 13.4, 18.3_

- [x] 2. Checkpoint - Database Layer Complete
  - Ensure all repository tests pass, ask the user if questions arise.

- [ ] 3. Security and Authentication Services
  - [x] 3.1 Implement EncryptionService
    - Create `src/services/encryption_service.py`
    - Use Fernet symmetric encryption from cryptography library
    - Implement `encrypt()` and `decrypt()` methods
    - Derive key from application secret
    - _Requirements: 4.2, 4.4_

  - [x] 3.2 Write property test for encryption round-trip
    - **Property 10: Credential Encryption Round-Trip**
    - **Validates: Requirements 4.2, 4.3, 4.4, 18.2**

  - [x] 3.3 Implement password hashing utilities
    - Create `src/services/password_utils.py`
    - Use bcrypt for password hashing
    - Implement `hash_password()` and `verify_password()` functions
    - _Requirements: 1.2, 18.1_

  - [x] 3.4 Write property test for password hashing
    - **Property 2: Password Hashing Security**
    - **Validates: Requirements 1.2, 18.1**

  - [x] 3.5 Implement SessionService
    - Create `src/services/session_service.py`
    - Implement `create_session()`, `get_current_session()`, `clear_session()`, `is_authenticated()` methods
    - Store session in memory
    - _Requirements: 3.1, 3.2, 3.4_

  - [x] 3.6 Write property test for session management
    - **Property 7: Session Persistence Across Navigation**
    - **Property 8: Logout Clears Session**
    - **Validates: Requirements 3.1, 3.2**

  - [x] 3.7 Implement AuthService
    - Create `src/services/auth_service.py`
    - Implement `register()` with validation, password hashing, and storage
    - Implement `login()` with credential verification and session creation
    - Implement `logout()` to clear session
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 3.2_

  - [x] 3.8 Write property tests for authentication
    - **Property 1: Registration Input Validation**
    - **Property 4: Registration Persistence Round-Trip**
    - **Property 5: Authentication Correctness**
    - **Property 6: Session Creation on Login**
    - **Validates: Requirements 1.1, 1.4, 2.1, 2.2, 2.3**

- [x] 4. Checkpoint - Authentication Services Complete
  - Ensure all authentication tests pass, ask the user if questions arise.

- [ ] 5. Broker Integration Services
  - [x] 5.1 Implement BrokerService
    - Create `src/services/broker_service.py`
    - Implement `save_credentials()` with encryption
    - Implement `get_credentials()` with decryption
    - Implement `has_credentials()` check
    - Implement `generate_oauth_url()` for Fyers OAuth
    - Implement `authenticate_broker()` using existing `fyers/api/auth_api.py`
    - Implement `store_access_token()`
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 5.1, 5.4, 5.5_

  - [x] 5.2 Write property test for OAuth URL generation
    - **Property 11: OAuth URL Generation**
    - **Validates: Requirements 5.1**

  - [x] 5.3 Implement TradingService
    - Create `src/services/trading_service.py`
    - Implement `get_funds()` using existing `fyers/api/funds.py`
    - Implement `get_positions()` using existing `fyers/api/order_api.py`
    - Implement `get_holdings()` using existing `fyers/api/order_api.py`
    - Implement `get_order_book()` using existing `fyers/api/order_api.py`
    - Implement `place_order()` using existing `fyers/api/order_api.py`
    - Implement `modify_order()` using existing `fyers/api/order_api.py`
    - Implement `cancel_order()` using existing `fyers/api/order_api.py`
    - Implement `close_all_positions()` using existing `fyers/api/order_api.py`
    - _Requirements: 6.1, 7.1, 8.1, 9.1, 10.5, 11.3, 12.2_

  - [x] 5.4 Write property test for order validation
    - **Property 21: Order Request Validation**
    - **Validates: Requirements 10.4**

  - [x] 5.5 Implement WatchlistService
    - Create `src/services/watchlist_service.py`
    - Implement `add_symbol()` with validation against master contract DB
    - Implement `remove_symbol()`
    - Implement `get_watchlist()`
    - Implement `search_symbols()` using existing `fyers/database/master_contract_db.py`
    - _Requirements: 13.1, 13.2, 13.4, 15.1_

  - [x] 5.6 Write property tests for watchlist
    - **Property 24: Symbol Validation for Watchlist**
    - **Property 25: Watchlist Add/Remove Round-Trip**
    - **Property 27: Watchlist Persistence Across Sessions**
    - **Validates: Requirements 13.1, 13.2, 13.4, 13.5**

  - [x] 5.7 Implement WebSocketService
    - Create `src/services/websocket_service.py`
    - Implement `connect()` using existing `fyers/streaming/` code
    - Implement `subscribe()` for price updates
    - Implement `unsubscribe()`
    - Implement `disconnect()`
    - Handle reconnection logic
    - _Requirements: 14.1, 14.2, 14.3, 14.4_

- [x] 6. Checkpoint - Services Layer Complete
  - Ensure all service tests pass, ask the user if questions arise.

- [ ] 7. UI Windows - Authentication Flow
  - [x] 7.1 Implement base window styles and utilities
    - Create `src/ui/styles.py` with consistent styling (colors, fonts, spacing)
    - Create `src/ui/utils.py` with helper functions for loading indicators, error display
    - Define Hindi-English label constants
    - _Requirements: 16.3_

  - [x] 7.2 Implement LoginWindow
    - Create `src/ui/windows/login_window.py`
    - Add username and password input fields
    - Add login button with validation
    - Add "Register" link to open registration
    - Emit `login_successful` signal on success
    - Display error messages for invalid credentials
    - _Requirements: 2.1, 2.2, 2.3, 16.1_

  - [x] 7.3 Implement RegisterWindow
    - Create `src/ui/windows/register_window.py`
    - Add username, password, confirm password, email fields
    - Add register button with validation
    - Validate email format
    - Display inline validation errors
    - Emit `registration_successful` signal on success
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 16.1_

  - [x] 7.4 Write property test for validation error highlighting
    - **Property 35: Validation Error Field Highlighting**
    - **Validates: Requirements 17.2**

  - [x] 7.5 Implement CredentialsWindow
    - Create `src/ui/windows/credentials_window.py`
    - Add API Key and API Secret input fields
    - Add "Authenticate with Fyers" button
    - Handle OAuth flow (open browser, capture callback)
    - Display authentication status
    - Emit `authentication_successful` signal with access token
    - _Requirements: 4.1, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

- [x] 8. Checkpoint - Authentication UI Complete
  - Ensure login, register, and credentials windows work correctly, ask the user if questions arise.

- [ ] 9. UI Widgets - Dashboard Components
  - [x] 9.1 Implement FundsWidget
    - Create `src/ui/widgets/funds_widget.py`
    - Display available cash, collateral, utilized margin
    - Display realized and unrealized P&L
    - Add refresh button
    - Show loading indicator during fetch
    - _Requirements: 6.2, 6.3, 6.4, 16.5_

  - [x] 9.2 Write property test for funds display completeness
    - **Property 12: Funds Data Display Completeness**
    - **Validates: Requirements 6.2, 6.3**

  - [x] 9.3 Implement PositionsWidget
    - Create `src/ui/widgets/positions_widget.py`
    - Display positions table with symbol, quantity, avg price, LTP, P&L
    - Add "Close" button for each position
    - Add "Close All" button
    - Show loading indicator during fetch
    - _Requirements: 7.2, 7.3, 7.4, 7.5_

  - [x] 9.4 Write property test for position display
    - **Property 13: Position Data Display Completeness**
    - **Property 14: Position Display Updates on Data Change**
    - **Validates: Requirements 7.2, 7.3**

  - [x] 9.5 Implement HoldingsWidget
    - Create `src/ui/widgets/holdings_widget.py`
    - Display holdings table with symbol, quantity, avg price, current value, P&L
    - Show loading indicator during fetch
    - _Requirements: 8.2, 8.3_

  - [x] 9.6 Write property test for holdings display
    - **Property 15: Holdings Data Display Completeness**
    - **Validates: Requirements 8.2**

  - [x] 9.7 Implement OrderBookWidget
    - Create `src/ui/widgets/order_book_widget.py`
    - Display orders table with order ID, symbol, type, quantity, price, status
    - Add "Modify" and "Cancel" buttons for pending orders
    - Visual differentiation for order statuses (colors/icons)
    - Show loading indicator during fetch
    - _Requirements: 9.2, 9.3, 9.4, 9.5_

  - [x] 9.8 Write property tests for order book display
    - **Property 16: Order Data Display Completeness**
    - **Property 17: Pending Order Actions Availability**
    - **Property 18: Order Status Visual Differentiation**
    - **Validates: Requirements 9.2, 9.3, 9.4**

  - [x] 9.9 Implement OrderFormWidget
    - Create `src/ui/widgets/order_form_widget.py`
    - Add fields: symbol, exchange dropdown, action (BUY/SELL), quantity, order type, product type, price, trigger price
    - Disable price field for Market orders
    - Enable and require price for Limit/SL orders
    - Validate all fields before submission
    - Emit `order_submitted` signal
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.6, 10.7_

  - [x] 9.10 Write property tests for order form
    - **Property 19: Market Order Price Field State**
    - **Property 20: Limit/SL Order Price Field State**
    - **Validates: Requirements 10.2, 10.3**

  - [x] 9.11 Implement OrderModifyDialog
    - Create `src/ui/widgets/order_modify_dialog.py`
    - Pre-populate form with current order values
    - Allow modification of quantity, price, trigger price
    - Validate modifications
    - _Requirements: 11.1, 11.2, 11.4, 11.5_

  - [x] 9.12 Write property test for order modification form
    - **Property 22: Order Modification Form Population**
    - **Property 23: Order Modification Validation**
    - **Validates: Requirements 11.1, 11.2**

- [x] 10. Checkpoint - Trading Widgets Complete
  - Ensure all trading widgets render correctly and handle data, ask the user if questions arise.

- [ ] 11. UI Widgets - Watchlist and Search
  - [x] 11.1 Implement SymbolSearchWidget
    - Create `src/ui/widgets/symbol_search_widget.py`
    - Add search input with autocomplete
    - Display results with symbol, name, exchange
    - Emit `symbol_selected` signal on selection
    - Show "No results" message when empty
    - _Requirements: 15.1, 15.2, 15.3, 15.4_

  - [x] 11.2 Write property test for symbol search
    - **Property 32: Symbol Search Results**
    - **Validates: Requirements 15.1, 15.2**

  - [x] 11.3 Implement WatchlistWidget
    - Create `src/ui/widgets/watchlist_widget.py`
    - Display watchlist table with symbol, LTP, change, change %
    - Add "Remove" button for each symbol
    - Add "Trade" button to open order form
    - Integrate with WebSocketService for live prices
    - Show stale indicator when WebSocket disconnected
    - _Requirements: 13.3, 14.1, 14.2, 14.3, 14.5_

  - [x] 11.4 Write property tests for watchlist widget
    - **Property 26: Watchlist Display Completeness**
    - **Property 28: WebSocket Subscription on Watchlist Display**
    - **Property 29: Real-Time Price Update Display**
    - **Property 30: WebSocket Unsubscription on Navigation**
    - **Property 31: Stale Price Indicator**
    - **Validates: Requirements 13.3, 14.1, 14.2, 14.3, 14.5**

- [x] 12. Checkpoint - Watchlist Widgets Complete
  - Ensure watchlist and search work with live data, ask the user if questions arise.

- [ ] 13. Dashboard Window and Integration
  - [x] 13.1 Implement DashboardWindow
    - Create `src/ui/windows/dashboard_window.py`
    - Add tabbed interface with tabs: Funds, Positions, Holdings, Orders, Watchlist
    - Add header with user info and logout button
    - Add symbol search in header
    - Integrate all widgets into tabs
    - Handle tab switching and data refresh
    - _Requirements: 16.2, 16.4_

  - [x] 13.2 Write property test for UI responsiveness
    - **Property 33: UI Responsiveness**
    - **Validates: Requirements 16.4**

  - [x] 13.3 Implement main application entry point
    - Create `src/main.py`
    - Initialize database on startup
    - Create QApplication
    - Implement window navigation flow (Login -> Credentials -> Dashboard)
    - Handle logout and return to login
    - _Requirements: 2.4, 3.3, 18.4_

  - [x] 13.4 Implement error handling and logging
    - Create `src/utils/logger.py` with logging configuration
    - Add error handling decorators for services
    - Implement user-friendly error message display
    - _Requirements: 17.1, 17.3, 17.4_

  - [x] 13.5 Write property test for error logging
    - **Property 36: Error Logging**
    - **Validates: Requirements 17.3**

  - [x] 13.6 Write property test for loading indicators
    - **Property 34: Loading Indicator Display**
    - **Validates: Requirements 16.5**

- [x] 14. Final Checkpoint - Full Integration
  - Ensure complete application flow works end-to-end, ask the user if questions arise.

- [ ] 15. Final Testing and Polish
  - [x] 15.1 Run all property-based tests
    - Execute all Hypothesis property tests with 100+ iterations
    - Fix any failing properties
    - _Requirements: All testable properties_

  - [x] 15.2 Manual integration testing
    - Test complete user flow: Register -> Login -> Add Credentials -> OAuth -> Dashboard
    - Test all trading operations with Fyers sandbox
    - Test watchlist with live WebSocket data
    - _Requirements: All requirements_

  - [x] 15.3 Code cleanup and documentation
    - Add docstrings to all public methods
    - Create README.md with setup and usage instructions
    - _Requirements: Documentation_

## Notes

- All tasks including property tests are required for comprehensive implementation
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties using Hypothesis library
- The implementation uses existing Fyers API code from `fyers/` directory without modification
- PySide6 signals/slots are used for loose coupling between components
