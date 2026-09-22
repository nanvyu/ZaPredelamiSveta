#include "ResearchPrototypeActor.h"

#include "ResearchInteractionComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "Engine/StaticMesh.h"
#include "Kismet/GameplayStatics.h"

AResearchPrototypeActor::AResearchPrototypeActor()
{
	PrimaryActorTick.bCanEverTick = false;

	SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
	SetRootComponent(SceneRoot);

	Mesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("PrototypeMesh"));
	Mesh->SetupAttachment(SceneRoot);
	Mesh->SetCollisionProfileName(TEXT("BlockAll"));

	StatusLight = CreateDefaultSubobject<UPointLightComponent>(TEXT("StatusLight"));
	StatusLight->SetupAttachment(SceneRoot);
	StatusLight->SetRelativeLocation(FVector(0.0, 0.0, 120.0));
	StatusLight->SetAttenuationRadius(450.0f);
	StatusLight->SetIntensity(5000.0f);

	Label = CreateDefaultSubobject<UTextRenderComponent>(TEXT("Label"));
	Label->SetupAttachment(SceneRoot);
	Label->SetRelativeLocation(FVector(0.0, 0.0, 180.0));
	Label->SetRelativeRotation(FRotator(0.0, 180.0, 0.0));
	Label->SetHorizontalAlignment(EHTA_Center);
	Label->SetWorldSize(34.0f);
	Label->SetTextRenderColor(FColor::White);
}

void AResearchPrototypeActor::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);
	ApplyRoleAppearance();
}

void AResearchPrototypeActor::ApplyRoleAppearance()
{
	const TCHAR* MeshPath = TEXT("/Engine/BasicShapes/Cube.Cube");
	FVector Scale(1.0);
	FLinearColor LightColor = FLinearColor::White;
	FString DisplayName;

	switch (PrototypeRole)
	{
	case EResearchPrototypeRole::Organism:
		MeshPath = TEXT("/Engine/BasicShapes/Sphere.Sphere");
		Scale = FVector(1.25, 1.25, 1.8);
		LightColor = FLinearColor(0.15f, 0.9f, 0.75f);
		DisplayName = TEXT("UNKNOWN LUMINOUS ORGANISM");
		break;
	case EResearchPrototypeRole::SalvageCoil:
		MeshPath = TEXT("/Engine/BasicShapes/Cylinder.Cylinder");
		Scale = FVector(0.65, 0.65, 0.35);
		LightColor = FLinearColor(1.0f, 0.5f, 0.05f);
		DisplayName = TEXT("DAMAGED FIELD COIL");
		break;
	case EResearchPrototypeRole::MobileLab:
		Scale = FVector(3.8, 2.4, 1.4);
		LightColor = bPowered ? FLinearColor::Green : FLinearColor::Red;
		DisplayName = bPowered ? TEXT("MOBILE LAB: POWER RESTORED") : TEXT("MOBILE LAB: POWER FAILURE");
		break;
	case EResearchPrototypeRole::ExitBeacon:
		Scale = FVector(0.8, 0.8, 4.5);
		LightColor = bPowered ? FLinearColor::Green : FLinearColor(0.08f, 0.08f, 0.08f);
		DisplayName = bPowered ? TEXT("ROUTE UNLOCKED") : TEXT("INACTIVE ROUTE BEACON");
		break;
	}

	if (UStaticMesh* Shape = LoadObject<UStaticMesh>(nullptr, MeshPath))
	{
		Mesh->SetStaticMesh(Shape);
	}
	Mesh->SetRelativeScale3D(Scale);
	StatusLight->SetLightColor(LightColor);
	StatusLight->SetIntensity((PrototypeRole == EResearchPrototypeRole::ExitBeacon && !bPowered) ? 0.0f : 5000.0f);
	Label->SetText(FText::FromString(DisplayName));
	Label->SetRelativeLocation(FVector(0.0, 0.0,
		PrototypeRole == EResearchPrototypeRole::MobileLab ? 220.0 : 180.0));
}

void AResearchPrototypeActor::HandleAnalyze(UResearchInteractionComponent* Researcher)
{
	if (!Researcher || PrototypeRole != EResearchPrototypeRole::Organism)
	{
		return;
	}

	if (!Researcher->HasAnalyzedOrganism())
	{
		Researcher->MarkOrganismAnalyzed();
		Label->SetText(FText::FromString(TEXT("BIOELECTRIC ACCUMULATOR")));
		StatusLight->SetLightColor(FLinearColor(0.2f, 0.55f, 1.0f));
	}
	else
	{
		Researcher->ShowMessage(TEXT("Analysis already recorded: charge peaks after a stable pulse."));
	}
}

void AResearchPrototypeActor::HandleInteract(UResearchInteractionComponent* Researcher)
{
	if (!Researcher)
	{
		return;
	}

	switch (PrototypeRole)
	{
	case EResearchPrototypeRole::Organism:
		if (!Researcher->HasAnalyzedOrganism())
		{
			Researcher->ShowMessage(TEXT("The organism retracts. Analyze its rhythm before touching it."));
		}
		else if (!bConsumed)
		{
			bConsumed = true;
			Researcher->CollectBioCell();
			Label->SetText(FText::FromString(TEXT("ORGANISM: SAMPLE EXTRACTED")));
			StatusLight->SetIntensity(900.0f);
		}
		break;

	case EResearchPrototypeRole::SalvageCoil:
		if (!bConsumed)
		{
			bConsumed = true;
			Researcher->CollectCoil();
			SetActorHiddenInGame(true);
			SetActorEnableCollision(false);
		}
		break;

	case EResearchPrototypeRole::MobileLab:
		if (!bPowered && Researcher->TryRepairLab())
		{
			SetPowered(true);

			TArray<AActor*> PrototypeActors;
			UGameplayStatics::GetAllActorsOfClass(this, StaticClass(), PrototypeActors);
			for (AActor* Actor : PrototypeActors)
			{
				if (AResearchPrototypeActor* PrototypeActor = Cast<AResearchPrototypeActor>(Actor))
				{
					if (PrototypeActor->PrototypeRole == EResearchPrototypeRole::ExitBeacon)
					{
						PrototypeActor->SetPowered(true);
					}
				}
			}
		}
		break;

	case EResearchPrototypeRole::ExitBeacon:
		Researcher->ShowMessage(bPowered
			? TEXT("The restored laboratory transmits a stable route signal.")
			: TEXT("The beacon has no power. Repair the mobile laboratory first."));
		break;
	}
}

void AResearchPrototypeActor::SetPowered(bool bNewPowered)
{
	bPowered = bNewPowered;
	ApplyRoleAppearance();
}

FString AResearchPrototypeActor::GetInteractionPrompt(const UResearchInteractionComponent* Researcher) const
{
	if (!Researcher)
	{
		return FString();
	}

	switch (PrototypeRole)
	{
	case EResearchPrototypeRole::Organism:
		return Researcher->HasAnalyzedOrganism()
			? (bConsumed ? TEXT("[Q] Review organism analysis") : TEXT("[E] Extract charged cell   [Q] Review analysis"))
			: TEXT("[Q] Analyze unknown organism");
	case EResearchPrototypeRole::SalvageCoil:
		return bConsumed ? FString() : TEXT("[E] Take damaged field coil");
	case EResearchPrototypeRole::MobileLab:
		return bPowered ? TEXT("Mobile laboratory is operational") : TEXT("[E] Attempt improvised power repair");
	case EResearchPrototypeRole::ExitBeacon:
		return bPowered ? TEXT("Route beacon online - prototype complete") : TEXT("Exit beacon has no power");
	}

	return FString();
}
