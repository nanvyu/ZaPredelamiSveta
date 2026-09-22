#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "ResearchPrototypeActor.generated.h"

class UPointLightComponent;
class UResearchInteractionComponent;
class UStaticMeshComponent;
class UTextRenderComponent;

UENUM(BlueprintType)
enum class EResearchPrototypeRole : uint8
{
	Organism UMETA(DisplayName="Energy Organism"),
	SalvageCoil UMETA(DisplayName="Salvage Coil"),
	MobileLab UMETA(DisplayName="Mobile Laboratory"),
	ExitBeacon UMETA(DisplayName="Exit Beacon")
};

UCLASS(Blueprintable)
class ZAPREDELAMISVETA_API AResearchPrototypeActor : public AActor
{
	GENERATED_BODY()

public:
	AResearchPrototypeActor();

	virtual void OnConstruction(const FTransform& Transform) override;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Research Prototype")
	EResearchPrototypeRole PrototypeRole = EResearchPrototypeRole::Organism;

	UFUNCTION(BlueprintCallable, Category="Research Prototype")
	void HandleAnalyze(UResearchInteractionComponent* Researcher);

	UFUNCTION(BlueprintCallable, Category="Research Prototype")
	void HandleInteract(UResearchInteractionComponent* Researcher);

	UFUNCTION(BlueprintCallable, Category="Research Prototype")
	void SetPowered(bool bNewPowered);

	FString GetInteractionPrompt(const UResearchInteractionComponent* Researcher) const;
	EResearchPrototypeRole GetRole() const { return PrototypeRole; }

private:
	UPROPERTY(VisibleAnywhere, Category="Components")
	USceneComponent* SceneRoot;

	UPROPERTY(VisibleAnywhere, Category="Components")
	UStaticMeshComponent* Mesh;

	UPROPERTY(VisibleAnywhere, Category="Components")
	UPointLightComponent* StatusLight;

	UPROPERTY(VisibleAnywhere, Category="Components")
	UTextRenderComponent* Label;

	UPROPERTY(Transient)
	bool bConsumed = false;

	UPROPERTY(Transient)
	bool bPowered = false;

	void ApplyRoleAppearance();
};
