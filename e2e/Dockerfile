# Clean Debian. curl + python3 are the base install a user would have.
# The advertised one-liner is what this image then runs, against a
# local origin (the checkout bind-mounted at /opt/origin).
FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl python3 \
 && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash tester
COPY inside.sh /usr/local/bin/spp-e2e
RUN chmod 755 /usr/local/bin/spp-e2e

USER tester
ENV HOME=/home/tester
WORKDIR /home/tester
ENTRYPOINT ["/usr/local/bin/spp-e2e"]
