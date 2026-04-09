"""
COPY THE TEXT BELOW AND SAVE IT AS 'README.md'
"""

# Google Cloud Console Setup for Calendar API

Follow these steps to generate the `credentials.json` file required for `waste_scraper.py`.

### 1. Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Click the **Project Dropdown** (top left, next to "Google Cloud") and select **New Project**.
3. Name it `Bin-Collection-Sync` and click **Create**.
4. Ensure your new project is selected in the dropdown.

### 2. Enable the Google Calendar API

1. In the left-hand sidebar, go to **APIs & Services** > **Enabled APIs & Services**.
2. Click **+ ENABLE APIS AND SERVICES** at the top.
3. Search for **"Google Calendar API"**.
4. Click on the result and then click **Enable**.

### 3. Configure the OAuth Consent Screen

*Google needs to know who is asking for permission.*

1. Go to **APIs & Services** > **OAuth consent screen**.
2. Select **External** (if you aren't using a Workspace/Business account) and click **Create**.
3. Fill in the required fields:
   * **App name**: `Bin Scraper`
   * **User support email**: Your email
   * **Developer contact info**: Your email
4. Click **Save and Continue** through the "Scopes" page (no changes needed).
5. On the **Test users** screen, click **+ ADD USERS** and add your own Gmail address. **Crucial**: The script will only work for accounts listed here while the app is in "Testing" mode.

### 4. Create Credentials

1. Go to **APIs & Services** > **Credentials**.
2. Click **+ Create Credentials** at the top and select **OAuth client ID**.
3. For **Application type**, select **Desktop app**.
4. Name it `Bin Desktop Client` and click **Create**.
5. You will see a "OAuth client created" popup. Click **DOWNLOAD JSON**.
6. **IMPORTANT**: Rename the downloaded file to `credentials.json` and move it into the same folder as your `waste_scraper.py` script.

### 5. Running for the First Time

1. Ensure you have installed the libraries:
   ```bash
   pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
   ```
2. Run your script: `python waste_scraper.py`.
3. A browser window will automatically open.
4. Select your Google Account.
5. **Warning Screen**: You will likely see "Google hasn't verified this app". Click **Advanced** > **Go to Bin Scraper (unsafe)** to proceed.
6. Grant permission to **"See, edit, share, and permanently delete all the calendars you can access using Google Calendar"**.
7. Once finished, the browser will say "The authentication flow has completed," and a `token.pickle` file will appear in your folder.

### Troubleshooting

* **"Access Blocked: Project has not been configured"**: Ensure you added your email to the **Test users** section in Step 3.
* **"File not found: credentials.json"**: Make sure the file is in the exact same directory from which you are running the Python command.
* **Token Errors**: If you change permissions or projects, delete `token.pickle` and run the script again to re-authenticate.

**Note**: The `token.pickle` file allows you to run the script in the future without logging in again.