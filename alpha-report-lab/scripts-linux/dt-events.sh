#!/bin/bash
# dt-events.sh — Dynatrace Events API v2 helper for task scripts.
#
# Source this from a task script:
#     source "$(dirname "$0")/dt-events.sh"
#
# Then wrap work with:
#     dt_run "install" "$SCRIPTS_DIR/install.sh"
#
# Reads DT_ENV_URL and DT_API_TOKEN from the environment, falling back to
# alpha-engine/.env. The API token MUST have the `events.ingest` scope.
# All event pushes are best-effort: failures never break the wrapped task.

_DT_EVENTS_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

_dt_load_env() {
    if [ -z "$DT_ENV_URL" ] || [ -z "$DT_API_TOKEN" ]; then
        local env_file="$_DT_EVENTS_ROOT/alpha-engine/.env"
        if [ -f "$env_file" ]; then
            # shellcheck disable=SC2046
            while IFS='=' read -r key val; do
                case "$key" in
                    \#*|"") continue ;;
                esac
                key="$(echo "$key" | tr -d ' ')"
                val="$(echo "$val" | sed 's/^ *//;s/ *$//')"
                if [ "$key" = "DT_ENV_URL"   ] && [ -z "$DT_ENV_URL"   ]; then export DT_ENV_URL="$val";   fi
                if [ "$key" = "DT_API_TOKEN" ] && [ -z "$DT_API_TOKEN" ]; then export DT_API_TOKEN="$val"; fi
            done < "$env_file"
        fi
    fi
}

# dt_send_event <eventType> <title> [propsJsonFragment]
# propsJsonFragment example: '"task.name":"install","task.status":"success"'
dt_send_event() {
    local event_type="$1"
    local title="$2"
    local props="$3"

    _dt_load_env
    if [ -z "$DT_ENV_URL" ] || [ -z "$DT_API_TOKEN" ]; then
        echo "  [dt-events] DT_ENV_URL/DT_API_TOKEN not set — skipping push."
        return 0
    fi

    local endpoint="${DT_ENV_URL%/}/api/v2/events/ingest"
    local body
    body=$(printf '{"eventType":"%s","title":%s,"properties":{%s}}' \
        "$event_type" \
        "$(printf '%s' "$title" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))' 2>/dev/null || echo "\"$title\"")" \
        "$props")

    if command -v curl >/dev/null 2>&1; then
        curl -sS -o /dev/null -w "" --max-time 10 \
            -X POST "$endpoint" \
            -H "Authorization: Api-Token $DT_API_TOKEN" \
            -H "Content-Type: application/json" \
            --data "$body" \
            && echo "  [dt-events] $event_type pushed: $title" \
            || echo "  [dt-events] push failed (non-fatal)"
    else
        echo "  [dt-events] curl not installed — skipping push."
    fi
}

# dt_run <task_name> <command...>
dt_run() {
    local task_name="$1"; shift
    local host_name user_name start_iso
    host_name="$(hostname)"
    user_name="${USER:-$(id -un)}"
    start_iso="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

    local base_props
    base_props=$(printf '"task.name":"%s","task.host":"%s","task.user":"%s","task.os":"linux","task.shell":"bash","lab.component":"tasks-runner","lab.script":"tasks.sh","task.start_utc":"%s"' \
        "$task_name" "$host_name" "$user_name" "$start_iso")

    dt_send_event "CUSTOM_INFO" \
        "alpha-report-lab task: $task_name started" \
        "$base_props,\"task.status\":\"started\""

    local start_epoch end_epoch duration status event_type exit_code
    start_epoch=$(date +%s)
    "$@"
    exit_code=$?
    end_epoch=$(date +%s)
    duration=$(( end_epoch - start_epoch ))

    if [ "$exit_code" -eq 0 ]; then
        status="success"; event_type="CUSTOM_INFO"
    else
        status="failure"; event_type="ERROR_EVENT"
    fi

    local end_iso
    end_iso="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    dt_send_event "$event_type" \
        "alpha-report-lab task: $task_name $status (${duration}s)" \
        "$base_props,\"task.status\":\"$status\",\"task.exit_code\":\"$exit_code\",\"task.duration_seconds\":\"$duration\",\"task.end_utc\":\"$end_iso\""

    return "$exit_code"
}
