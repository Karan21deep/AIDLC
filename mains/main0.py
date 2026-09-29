import json
import os

from dotenv import load_dotenv

from agents.repository_discovery_agent import (
    RepositoryDiscoveryAgent
)


def main():

    load_dotenv()

    repo_path = input(
        "Enter repository path: "
    ).strip()

    agent = RepositoryDiscoveryAgent()

    report = agent.run(
        repo_path
    )

    os.makedirs(
        "output",
        exist_ok=True
    )

    output_file = (
        "output/discovery_report.json"
    )

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            report.model_dump(),
            f,
            indent=2
        )

    print(
        "\nRepository discovery completed."
    )

    print(
        f"Report saved to: {output_file}"
    )

    print(
        "\nSummary:"
    )

    print(
        report.summary
    )


if __name__ == "__main__":
    main()