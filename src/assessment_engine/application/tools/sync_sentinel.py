import logging
import sys

from assessment_engine.infrastructure.streaming_sentinel import StreamingSentinel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sync_sentinel")


def main() -> None:
    """Manually triggers the on-demand synchronization of the Streaming Sentinel queue,
    ingesting all pending items and updating the Raptor RAG Tree.
    """
    client_id = sys.argv[1] if len(sys.argv) > 1 else "redeia_v3"

    logger.info(f"🔄 Starting On-Demand Sentinel Sync for client: {client_id}")

    sentinel = StreamingSentinel(client_id=client_id)
    sentinel.initialize_queue()

    try:
        # Process up to 50 pending items in a single, efficient, ACID-compliant batch
        processed = sentinel.process_next_batch(batch_size=50)

        if processed > 0:
            logger.info(f"✓ Processed {processed} pending evidence items.")
            # Force trigger the dampened scheduler to immediately rebuild the Raptor Tree
            # by pretending we hit a quiet period
            sentinel.last_ingest_time = 0.0  # Force quiet period timeout
            triggered = sentinel.check_and_trigger_dampened_rebuild()
            if triggered:
                logger.info(
                    "✓ Raptor RAG Knowledge Tree successfully rebuilt and synchronized."
                )
        else:
            logger.info(
                "🟢 No pending evidence items in the queue. Everything is up to date!"
            )

    except Exception as e:
        logger.error(f"❌ Synchronization failed: {e}")
        sys.exit(1)
    finally:
        sentinel.close()

    logger.info("Sync completed successfully.")


if __name__ == "__main__":
    main()
