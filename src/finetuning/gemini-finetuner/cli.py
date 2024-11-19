import os
import argparse
import pandas as pd
import json
import time
import glob
from google.cloud import storage
import vertexai
from vertexai.preview.tuning import sft
from vertexai.generative_models import GenerativeModel, GenerationConfig
from google.oauth2 import service_account


def train(wait_for_job=False):
    print("train()")

    # Supervised Fine Tuning
    sft_tuning_job = sft.train(
        source_model=GENERATIVE_SOURCE_MODEL,
        train_dataset=TRAIN_DATASET,
        validation_dataset=VALIDATION_DATASET,
        epochs=10,  # change to 2-3
        adapter_size=4,
        learning_rate_multiplier=1.0,
        tuned_model_display_name="GlobalCollab-FineTuned-Model",
    )
    print("Training job started. Monitoring progress...\n\n")

    # Wait and refresh
    time.sleep(60)
    sft_tuning_job.refresh()

    if wait_for_job:
        print("Check status of tuning job:")
        print(sft_tuning_job)
        while not sft_tuning_job.has_ended:
            time.sleep(60)
            sft_tuning_job.refresh()
            print("Job in progress...")

    print(f"Tuned model name: {sft_tuning_job.tuned_model_name}")
    print(f"Tuned model endpoint name: {sft_tuning_job.tuned_model_endpoint_name}")
    print(f"Experiment: {sft_tuning_job.experiment}")


def chat():
    print("chat()")
    # Get the model endpoint from Vertex AI: https://console.cloud.google.com/vertex-ai/studio/tuning?project=ac215-project
    # MODEL_ENDPOINT = "projects/129349313346/locations/us-central1/endpoints/810191635601162240"
    # MODEL_ENDPOINT = "projects/129349313346/locations/us-central1/endpoints/5584851665544019968"
    MODEL_ENDPOINT = "projects/129349313346/locations/us-central1/endpoints/3319822527953371136"  # Finetuned model

    generative_model = GenerativeModel(MODEL_ENDPOINT)

    query = "How to solve homelessness?"
    print("query: ", query)
    response = generative_model.generate_content(
        [query],  # Input prompt
        generation_config=generation_config,  # Configuration settings
        stream=False,  # Enable streaming for responses
    )
    generated_text = response.text
    print("Fine-tuned LLM Response:", generated_text)


def main(args=None):
    print("CLI Arguments:", args)

    if args.train:
        train()

    if args.chat:
        chat()


if __name__ == "__main__":
    # Generate the inputs arguments parser
    # if you type into the terminal '--help', it will provide the description

    # Setup
    GCP_PROJECT = os.environ["GCP_PROJECT"]
    TRAIN_DATASET = (
        "gs://dataset-ai-research/train_annotated.jsonl"  # Replace with your dataset
    )
    VALIDATION_DATASET = (
        "gs://dataset-ai-research/val_annotated.jsonl"  # Replace with your dataset
    )
    GCP_LOCATION = "us-central1"
    GENERATIVE_SOURCE_MODEL = "gemini-1.5-flash-002"  # gemini-1.5-pro-002
    # Configuration settings for the content generation
    generation_config = {
        "max_output_tokens": 3000,  # Maximum number of tokens for output
        "temperature": 0.75,  # Control randomness in output
        "top_p": 0.95,  # Use nucleus sampling
    }

    credentials = service_account.Credentials.from_service_account_file(
        "secrets/ai-research-for-good-b6f4173936f9.json"
    )

    vertexai.init(project=GCP_PROJECT, location=GCP_LOCATION, credentials=credentials)

    parser = argparse.ArgumentParser(description="CLI")

    parser.add_argument(
        "--train",
        action="store_true",
        help="Train model",
    )
    parser.add_argument(
        "--chat",
        action="store_true",
        help="Chat with model",
    )

    args = parser.parse_args()

    main(args)
