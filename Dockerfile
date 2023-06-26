FROM python:3.11-alpine as base

# Build
FROM base as builder
COPY . /source
RUN python -m venv /venv
RUN /venv/bin/pip install /source

# Run
FROM base as runner
COPY --from=builder /venv /venv
ENTRYPOINT ["/venv/bin/netbox-kea-dhcp"]