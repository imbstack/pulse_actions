import logging
from mozci.mozci import trigger_missing_jobs_for_revision, trigger_all_talos_jobs
from thclient import TreeherderClient
from pulse_actions.publisher import MessageHandler

logging.basicConfig(format='%(levelname)s:\t %(message)s')
LOG = logging.getLogger()
MEMORY_SAVING_MODE = True

def on_resultset_action_event(data, message, dry_run):
    repo_name = data["project"]
    action = data["action"]
    times = data["times"]
    # Pulse gives us resultset_id, we need to get revision from it.
    resultset_id = data["resultset_id"]
    treeherder_client = TreeherderClient()
    revision = treeherder_client.get_resultsets(repo_name, id=resultset_id)[0]["revision"]
    status = None

    if action == "trigger_missing_jobs":
        LOG.info("trigger_missing_jobs requested by %s" % data["requester"])
        trigger_missing_jobs_for_revision(repo_name, revision, dry_run=dry_run)
        if not dry_run:
            status = 'trigger_missing_jobs request sent'
        else:
            status = 'Dry-mode, no request sent'
    elif action == "trigger_all_talos_jobs":
        LOG.info("trigger_all_talos_jobs requested by %s" % data["requester"])
        trigger_all_talos_jobs(repo_name, revision, times, dry_run=dry_run)
        if not dry_run:
            status = 'trigger_all_talos_jobs %s times request sent' % times
        else:
            status = 'Dry-mode, no request sent'
    # Send a pulse message showing what we did
    message_sender = MessageHandler()
    pulse_message = {
        'resultset_id': resultset_id,
        'action': action,
        'requester': data['requester'],
        'status': status}
    routing_key = '{}.{}'.format(repo_name, action)
    message_sender.publish_message(pulse_message, routing_key)
    # We need to ack the message to remove it from our queue
    message.ack()
