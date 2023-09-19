
# Wall API with Django Rest Framework

## A Platform for Advertisements

This platform empowers users with the ability to both view advertisements posted by others and create their own.

When it comes to creating ads, users are provided with a monthly free quota, allowing them to post a certain number of advertisements each month at no cost. If users wish to create more ads than their monthly free quota allows, they have the option to purchase ad tokens. Each ad token allows users to create one additional ad, providing flexibility to meet specific needs and goals. Ad tokens sell in packages.

Advertisements within the platform have an expiration date and are subject to soft deletion after reaching this expiration date. This ensures that outdated advertisements are automatically removed from the platform.

Additionally, the platform ensures secure user registration by verifying their identity through OTP (One-Time Password) sent to the user's entered phone number.




## Installation

To set up and run the Wall API project, please follow these installation instructions:

1. **Create a .env File:**
   Create a `.env` file in the project's root directory and configure the following environment variables:

   ```plaintext
   DOCKER_COMPOSE_DJANGO_SECRET_KEY=your-secret-key
   DOCKER_COMPOSE_DJANGO_DEBUG=debug-value
   DOCKER_AD_TOKEN_PRICE=price-for-each-ad-token
   ```

2. **Configure settings.py:**
   Open the project's `settings.py` file and customize other settings as needed, including those related to user login, OTP, ads, and discounts. Here are the settings you can configure:

   ```python
   # CustomUser
   MAX_LOGIN = 5  # Maximum success login before blocking the user
   LOGIN_SUCCESS_CHECK_PERIOD_MINUTE = 60  # Period (in minutes) to check for successful logins
   BLOCK_TIME_MAX_LOGIN_MINUTE = 15  # Maximum time (in minutes) a user is blocked after reaching the maximum successful login attempts

   # Config for OTP (One-Time Password) verification
   MAX_OTP_TRY = 3  Maximum number of OTP (One-Time Password) SMS sending attempts before getting restricted.
   RESET_TIME_OTP_MINUTE = 5  # Time (in minutes) within which OTP resetting is allowed
   LIMIT_TIME_MAX_OTP = 10  # Time limit (in minutes) for restricting a user from requesting to resend OTP after reaching the maximum resend OTP attempts.

   # Config for ads
   FREE_ADS_MONTHLY_QUOTA = 10  # Limit for creating ads in the monthly free quota
   MIN_REPORTS_TO_BLOCK_AD = 3  # Minimum reports required to block an ad
   AD_EXPIRY_PERIOD_DAYS = 30  # Expiry period (in days) for advertisements

   # Maximum Discount Percentage
   MAX_DISCOUNT_PERCENT = 30  # Maximum allowable discount percentage for a package
   ```

3. **Run Docker Compose:**
   Start the Docker containers using Docker Compose:
   ```bash
   docker-compose up 
   ```

4. **Migrate Database:**
    
    Make migrations:
    ```bash
   docker-compose exec web python manage.py makemigrations
   ```

   Apply database migrations:
   ```bash
   docker-compose exec web python manage.py migrate
   ```

5. **Create a Superuser (Optional):**

   If necessary, create a superuser for accessing the Django admin panel:
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

6. **Access the API:**

   The API should now be accessible at `http://localhost:8000/`. You can explore the API endpoints and interact with your project.

Replace `your-secret-key`, `debug-value`, and `price-for-each-ad-token` with your desired values. Adjust the settings in `settings.py` as needed for your project.


## Third-Party Apps

The project relies on several third-party apps to extend its functionality:

- **Django Axes**: Enhances security with login attempt monitoring.

- **Celery**: Used for background tasks. Check the "ads" app for Celery tasks defined in tasks.py.

- **Drf Spectacular**: Provides API documentation generation.

- **Rest Framework Simple JWT**: Implements JSON Web Token authentication for your API.

- **Django OTP**: Adds One-Time Password (OTP) functionality to the project for secure user verification.


These apps are included in the project by default, but you can customize their configurations as needed in the project's settings.



## Endpoints

### Admin Interface:
- `/admin/`

### API Documentation:
- Swagger UI: `/api/swagger/`

### Home Page:
- `/home/`

### Accounts:
- Login: `/accounts/login/`
- Check Code: `/accounts/login/check-code/`
- Logout: `/accounts/logout/`
- Login API: `/accounts/login/api/`
- Check Code API: `/accounts/login/check-code/api/`
- Refresh Token API: `/accounts/refresh/api/`
- User Profile API: `/accounts/profile/api/`
- Edit User Profile API: `/accounts/profile/edit/api/`

### Ads:
- List Ads: `/ads/list/`
- Search Ads: `/ads/search/`
- List Categories: `/ads/list/category/`
- List Ads by Category: `/ads/category/<int:pk>/`
- Create Ad: `/ads/create/`
- Ad Detail: `/ads/<int:pk>/`
- Report Ad: `/ads/report/<int:pk>/`
- Update Ad: `/ads/update/<int:pk>/`
- Delete Ad: `/ads/delete/<int:pk>/`
- Sign Ad: `/ads/sign/<int:pk>/`
- User's Signed Ads: `/ads/sign/list/`

### Payment:
- Checkout: `/payment/checkout/`
- Payment Callback: `/payment/callback/`
- List Ad Token Packages: `/payment/package/list/`
- Order Registration: `/payment/order/registration/`
- List User's Orders: `/payment/order/list/`
- Order Detail: `/payment/order/<int:pk>/`
- Update Order: `/payment/order/update/<int:pk>/`
