# Sprout Development Roadmap

This is the active development branch. For the stable v1.0 portfolio version, see the [`sprout-v1-final`](https://github.com/reallyreallyryan/sprout-v1/tree/sprout-v1-final) branch.

## Version History

- **v1.0.0** (July 2025) - Initial release with ML pipeline
  - 99.2% prediction accuracy
  - Autonomous watering system
  - Complete documentation

## Upcoming Features

### v1.1 (In Development)
- [ ] Real-time ML predictions (use model during operation)
- [ ] Multi-plant support with individual profiles
- [ ] Web dashboard for remote monitoring
- [ ] Water reservoir level detection

### v1.2 (Planned)
- [ ] Temperature and humidity sensors
- [ ] Email/SMS notifications
- [ ] Historical data API
- [ ] Plant health scoring

### v2.0 (Future)
- [ ] Computer vision for plant health
- [ ] Weather API integration
- [ ] Mobile app
- [ ] Cloud sync (optional)

## Contributing

To work on new features:
1. Create a feature branch: `git checkout -b feature/feature-name`
2. Make your changes
3. Submit a pull request to `main`

## Testing New Features

```bash
# Run system tests
python3 -m pytest tests/

# Test hardware components
python3 tests/test_watering.py
