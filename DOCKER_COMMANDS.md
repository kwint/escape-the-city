# Docker Commands Reference

Quick reference for common Docker commands for managing the Escape The City application.

## Basic Commands

### Start the application
```bash
docker-compose up -d
```

### Stop the application
```bash
docker-compose down
```

### Restart the application
```bash
docker-compose restart
```

### View logs
```bash
# Follow logs in real-time
docker-compose logs -f

# View last 100 lines
docker-compose logs --tail=100

# View logs for specific time period
docker-compose logs --since 1h
```

## Database & Data Management

### Create superuser
```bash
docker-compose exec web uv run python manage.py createsuperuser
```

### Run migrations
```bash
docker-compose exec web uv run python manage.py migrate
```

### Access Django shell
```bash
docker-compose exec web uv run python manage.py shell
```

### Backup database and media
```bash
# Create backup with timestamp
tar -czf backup-$(date +%Y%m%d-%H%M%S).tar.gz db/ media/
```

### Restore from backup
```bash
# Stop application
docker-compose down

# Extract backup (replace filename)
tar -xzf backup-20241122-150000.tar.gz

# Start application
docker-compose up -d
```

## Application Updates

### Update and rebuild
```bash
# Pull latest code
git pull

# Rebuild with no cache
docker-compose build --no-cache

# Restart with new image
docker-compose up -d
```

### Quick update (with cache)
```bash
git pull && docker-compose up -d --build
```

## Debugging

### Check container status
```bash
docker-compose ps
```

### View resource usage
```bash
docker stats escape-the-city
```

### Access container shell
```bash
docker-compose exec web /bin/bash
```

### View Django settings
```bash
docker-compose exec web uv run python manage.py diffsettings
```

### Test database connection
```bash
docker-compose exec web uv run python manage.py check --database default
```

## Data Management

### List all groups
```bash
docker-compose exec web uv run python manage.py shell -c "from hunt.models import Group; print(list(Group.objects.all()))"
```

### Clear all scans (testing)
```bash
docker-compose exec web uv run python manage.py shell -c "from hunt.models import Scan; Scan.objects.all().delete(); print('All scans deleted')"
```

### Export groups to JSON
```bash
docker-compose exec web uv run python manage.py dumpdata hunt.Group --indent 2 > groups_backup.json
```

### Import groups from JSON
```bash
cat groups_backup.json | docker-compose exec -T web uv run python manage.py loaddata --format=json -
```

## Cleanup

### Remove stopped containers
```bash
docker-compose rm
```

### Remove all data and start fresh
```bash
# WARNING: This deletes all data!
docker-compose down
rm -rf db/ media/
docker-compose up -d
docker-compose exec web uv run python manage.py createsuperuser
```

### Clean Docker system (free up space)
```bash
# Remove unused images
docker image prune -a

# Remove all unused data
docker system prune -a --volumes
```

## Monitoring

### Watch logs continuously
```bash
watch -n 1 'docker-compose logs --tail=20'
```

### Check disk usage
```bash
du -sh db/ media/
```

### Monitor HTTP requests (if logs show them)
```bash
docker-compose logs -f | grep "GET\|POST"
```

## Environment

### View current environment variables
```bash
docker-compose exec web env | grep DJANGO
```

### Test with different settings
```bash
# Temporarily enable debug mode
docker-compose exec -e DJANGO_DEBUG=True web uv run python manage.py check
```

## Production Tips

1. **Always use `-d` flag** to run in detached mode
2. **Check logs regularly** with `docker-compose logs -f`
3. **Backup before updates** using tar command above
4. **Monitor disk space** for `db/` and `media/` directories
5. **Restart after env changes** - changes to `.env` require restart

## Emergency Commands

### Force restart if container is stuck
```bash
docker-compose kill
docker-compose up -d
```

### Rebuild from scratch
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### View real-time performance
```bash
docker stats escape-the-city --no-stream
```
