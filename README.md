# Mereheze Wiki Contributor Bot

A Dockerized bot that automatically contributes to Mereheze wiki pages on a scheduled basis.

## Features

- Scheduled updates to multiple wiki pages
- Configuration via YAML file
- Docker container for easy deployment
- Automatic base image updates

## Configuration

Edit the `config/config.yaml` file to specify:
- Wiki URLs and credentials
- Pages to update
- Content to add
- Update schedules (in cron format)

## Deployment

### Docker CLI

1. Build the Docker image:
   ```bash
   docker build -t mereheze-wiki-contributor .

2. Run the container:
   ```bash
   docker run -d --name wiki-bot mereheze-wiki-contributor

### Docker Compose
   ```bash
   docker run -d --name mereheze-wiki-contributor \
     --restart always \
     -v /your-path/mereheze-wiki-contributor/config:/app/config/ \
     -e TZ=America/New_York \
     danutzzzzz/danutzzzzz/mereheze-wiki-contributor:latest
   ```

## Configuration

### Create Bot Account

Go to Special:BotPasswords, enter  the bot name and then select the Applicable grants:
   - Basic rights
   - High-volume (bot) access
   - Edit existing pages

## Manually Trigger
   ```bash
   python bot.py --wiki <Name> --url https://<URL> --user <Username>@<BotName> --token <YOUR_TOKEN>
   ```
## Implementation Notes

1. **Security**: The bot uses standard wiki login credentials. Make sure to:
   - Use a dedicated bot account with only necessary permissions
   - Never commit actual credentials to GitHub
   - Use secrets for Docker Hub credentials in GitHub Actions

2. **Scheduling**: The bot uses cron-style scheduling via the `schedule` library.

3. **Error Handling**: Basic error handling is included, but you may want to expand it for production use.

4. **Docker**: The Alpine-based image keeps the container small and secure.

5. **CI/CD**: The workflows handle both code updates and monthly base image refreshes.

To use this bot, you would:
1. Clone the repository
2. Configure the YAML file with your wiki details
3. Build and run the Docker container
4. Push to GitHub to trigger the CI/CD pipeline

Would you like me to elaborate on any particular aspect of this implementation?