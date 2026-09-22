#include "ResearchInteractionComponent.h"

#include "ResearchPrototypeActor.h"
#include "Engine/Engine.h"
#include "EngineUtils.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "InputCoreTypes.h"

UResearchInteractionComponent::UResearchInteractionComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
}

void UResearchInteractionComponent::BeginPlay()
{
	Super::BeginPlay();
	AddJournalEntry(TEXT("Expedition log: the mobile laboratory power system is destroyed."));
	ShowMessage(TEXT("PROTOTYPE: Observe the area, improvise a power source, and repair the lab."));
}

void UResearchInteractionComponent::TickComponent(float DeltaTime, ELevelTick TickType,
	FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	APawn* Pawn = Cast<APawn>(GetOwner());
	APlayerController* PC = Pawn ? Cast<APlayerController>(Pawn->GetController()) : nullptr;
	if (!PC || !Pawn->IsLocallyControlled())
	{
		return;
	}

	if (PC->WasInputKeyJustPressed(EKeys::J))
	{
		bJournalVisible = !bJournalVisible;
	}

	if (PC->WasInputKeyJustPressed(EKeys::Q))
	{
		if (AResearchPrototypeActor* Organism = FindClosest(700.0f, EResearchPrototypeRole::Organism))
		{
			Organism->HandleAnalyze(this);
		}
		else
		{
			ShowMessage(TEXT("Analyzer: no unknown biological signal in range."));
		}
	}

	if (PC->WasInputKeyJustPressed(EKeys::E))
	{
		if (AResearchPrototypeActor* Target = FindClosest(300.0f))
		{
			Target->HandleInteract(this);
		}
		else
		{
			ShowMessage(TEXT("Nothing usable within reach."));
		}
	}

	DrawPrototypeHUD();
}

AResearchPrototypeActor* UResearchInteractionComponent::FindClosest(float MaxDistance,
	TOptional<EResearchPrototypeRole> RequiredRole) const
{
	AResearchPrototypeActor* Closest = nullptr;
	float ClosestDistanceSq = FMath::Square(MaxDistance);
	const FVector OwnerLocation = GetOwner()->GetActorLocation();

	for (TActorIterator<AResearchPrototypeActor> It(GetWorld()); It; ++It)
	{
		AResearchPrototypeActor* Candidate = *It;
		if (RequiredRole.IsSet() && Candidate->GetRole() != RequiredRole.GetValue())
		{
			continue;
		}

		const float DistanceSq = FVector::DistSquared2D(OwnerLocation, Candidate->GetActorLocation());
		if (DistanceSq < ClosestDistanceSq)
		{
			ClosestDistanceSq = DistanceSq;
			Closest = Candidate;
		}
	}

	return Closest;
}

void UResearchInteractionComponent::MarkOrganismAnalyzed()
{
	if (bOrganismAnalyzed)
	{
		return;
	}

	bOrganismAnalyzed = true;
	AddJournalEntry(TEXT("Observation: the organism stores charge and releases it after a stable pulse."));
	ShowMessage(TEXT("NEW KNOWLEDGE: The organism can serve as a biological accumulator."));
}

void UResearchInteractionComponent::CollectBioCell()
{
	if (bHasBioCell)
	{
		return;
	}

	bHasBioCell = true;
	AddJournalEntry(TEXT("Component acquired: charged biological cell."));
	ShowMessage(TEXT("Acquired: charged biological cell."));
}

void UResearchInteractionComponent::CollectCoil()
{
	if (bHasCoil)
	{
		return;
	}

	bHasCoil = true;
	AddJournalEntry(TEXT("Component acquired: damaged field coil from an old research station."));
	ShowMessage(TEXT("Acquired: damaged field coil."));
}

bool UResearchInteractionComponent::TryRepairLab()
{
	if (bLabPowered)
	{
		ShowMessage(TEXT("The mobile laboratory is already operational."));
		return false;
	}

	if (!bHasCoil || !bHasBioCell)
	{
		FString Missing = TEXT("Repair requires:");
		if (!bHasCoil)
		{
			Missing += TEXT(" field coil;");
		}
		if (!bHasBioCell)
		{
			Missing += TEXT(" biological accumulator;");
		}
		ShowMessage(Missing);
		return false;
	}

	bLabPowered = true;
	AddJournalEntry(TEXT("Repair: the field coil now regulates power from the biological accumulator."));
	ShowMessage(TEXT("IMPROVISED REPAIR COMPLETE: Mobile laboratory power restored."));
	return true;
}

void UResearchInteractionComponent::ShowMessage(const FString& Message)
{
	if (GEngine)
	{
		GEngine->AddOnScreenDebugMessage(-1, 4.5f, FColor(120, 220, 255), Message);
	}
}

void UResearchInteractionComponent::AddJournalEntry(const FString& Entry)
{
	if (!JournalEntries.Contains(Entry))
	{
		JournalEntries.Add(Entry);
	}
}

FString UResearchInteractionComponent::GetObjectiveText() const
{
	if (!bHasCoil)
	{
		return TEXT("OBJECTIVE: Find a usable component among the abandoned equipment.");
	}
	if (!bOrganismAnalyzed)
	{
		return TEXT("OBJECTIVE: Analyze the luminous organism with [Q].");
	}
	if (!bHasBioCell)
	{
		return TEXT("OBJECTIVE: Carefully extract its charged cell with [E].");
	}
	if (!bLabPowered)
	{
		return TEXT("OBJECTIVE: Return to the mobile laboratory and install both components.");
	}
	return TEXT("PROTOTYPE COMPLETE: The route beacon is online.");
}

void UResearchInteractionComponent::DrawPrototypeHUD()
{
	if (!GEngine)
	{
		return;
	}

	GEngine->AddOnScreenDebugMessage(2101, 0.05f, bLabPowered ? FColor::Green : FColor::Yellow,
		GetObjectiveText());
	GEngine->AddOnScreenDebugMessage(2102, 0.05f, FColor::Silver,
		TEXT("Controls: [E] interact   [Q] analyze organism   [J] journal"));

	if (AResearchPrototypeActor* Nearby = FindClosest(320.0f))
	{
		const FString Prompt = Nearby->GetInteractionPrompt(this);
		if (!Prompt.IsEmpty())
		{
			GEngine->AddOnScreenDebugMessage(2103, 0.05f, FColor::Cyan, Prompt);
		}
	}

	if (bJournalVisible)
	{
		FString JournalText = TEXT("FIELD JOURNAL\n");
		for (const FString& Entry : JournalEntries)
		{
			JournalText += TEXT("- ") + Entry + TEXT("\n");
		}
		GEngine->AddOnScreenDebugMessage(2104, 0.05f, FColor(180, 235, 255), JournalText);
	}
}
