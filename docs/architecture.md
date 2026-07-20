# Architecture

RNAmining remains a synchronous PHP-to-Python application. Nginx exposes only `web/public/`; shared PHP fragments live in `web/templates/`. PHP invokes the installed Python CLI, whose implementation is in `src/rnamining/`, and loads versioned artifacts from `models/coding_prediction/`.

Scientific inputs and products are separated under `data/`. Browser examples are deliberately public under `web/public/examples/`. Web jobs are transient and isolated under `runtime/jobs/<execution-id>/{input,output,logs}`. Notebook and command-line evaluation runs belong under `outputs/evaluation/`. Both generated trees are ignored by Git.

`compose.local.yaml` publishes port 80. `compose.proxy.yaml` preserves the deployment that connects Nginx to the external `gatewayapps_proxy` network. Both mount only `web/public/` into Nginx.

