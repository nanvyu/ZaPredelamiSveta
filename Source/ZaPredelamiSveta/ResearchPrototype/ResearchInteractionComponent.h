#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "ResearchInteractionComponent.generated.h"

class AResearchPrototypeActor;
enum class EResearchPrototypeRole : uint8;

UCLASS(ClassGroup=(Research), meta=(BlueprintSpawnableComponent))
class ZAPREDELAMISVETA_API UResearchInteractionComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UResearchInteractionComponent();

	virtual void BeginPlay() override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType,
		FActorComponentTickFunction* ThisTickFunction) override;

	UFUNCTION(BlueprintCallable, Category="Research Prototype")
	void MarkOrganismAnalyzed();

	UFUNCTION(BlueprintCallable, Category="Research Prototype")
	void CollectBioCell();

	UFUNCTION(BlueprintCallable, Category="Research Prototype")
	void CollectCoil();

	UFUNCTION(BlueprintCallable, Category="Research Prototype")
	bool TryRepairLab();

	UFUNCTION(BlueprintCallable, Category="Research Prototype")
	void ShowMessage(const FString& Message);

	bool HasAnalyzedOrganism() const { return bOrganismAnalyzed; }
	bool HasBioCell() const { return bHasBioCell; }
	bool HasCoil() const { return bHasCoil; }
	bool IsLabPowered() const { return bLabPowered; }

private:
	UPROPERTY(Transient)
	bool bOrganismAnalyzed = false;

	UPROPERTY(Transient)
	bool bHasBioCell = false;

	UPROPERTY(Transient)
	bool bHasCoil = false;

	UPROPERTY(Transient)
	bool bLabPowered = false;

	UPROPERTY(Transient)
	bool bJournalVisible = false;

	UPROPERTY(Transient)
	TArray<FString> JournalEntries;

	AResearchPrototypeActor* FindClosest(float MaxDistance,
		TOptional<EResearchPrototypeRole> RequiredRole = TOptional<EResearchPrototypeRole>()) const;
	void AddJournalEntry(const FString& Entry);
	FString GetObjectiveText() const;
	void DrawPrototypeHUD();
};
