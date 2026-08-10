# Architecture

RNAmining remains a synchronous PHP-to-Python application. Nginx exposes only `web/public/`; shared PHP fragments live in `web/templates/`. PHP invokes `rnamining.cli` from the mounted `src/` tree and loads organism-specific artifacts from `models/coding_prediction/`. The offline generalist experiment stores its artifacts separately under `models/random_split/`.

Local development and the PHP image share the pinned Conda dependencies in `environment.yml`. Docker creates that environment inside the image; local users activate it and use `pip install -e .` to register the package and CLI against the source tree.

Scientific inputs and products are separated under `data/`. Browser examples are deliberately public under `web/public/examples/`. Web jobs are transient and isolated under `runtime/jobs/<execution-id>/{input,output,logs}`. Notebook and command-line evaluation runs belong under `outputs/evaluation/`. Both generated trees are ignored by Git.

`compose.local.yaml` publishes port 80. `compose.proxy.yaml` preserves the deployment that connects Nginx to the external `gatewayapps_proxy` network. Both mount only `web/public/` into Nginx.
