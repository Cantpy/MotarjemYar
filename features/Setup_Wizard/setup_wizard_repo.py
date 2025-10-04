# features/Setup_Wizard/setup_wizard_repo.py

from sqlalchemy.orm import Session
from shared.orm_models.users_models import (UsersModel, UserProfileModel, TranslationOfficeDataModel,
                                            SecurityQuestionModel)
from shared.orm_models.license_models import LicenseModel
from features.Setup_Wizard.setup_wizard_models import TranslationOfficeDTO, AdminUserDTO, AdminProfileDTO
import bcrypt


class SetupWizardRepository:
    """
    Stateless repository for setup wizard data operations.
    Requires a session to be passed into each method.
    """
    # === Existence Checks ===
    def is_license_present(self, session: Session) -> bool:
        return session.query(LicenseModel).first() is not None

    def is_office_present(self, session: Session) -> bool:
        return session.query(TranslationOfficeDataModel).first() is not None

    def is_admin_present(self, session: Session) -> bool:
        return session.query(UsersModel).filter(UsersModel.role == 'admin').first() is not None

    # === Data Persistence ===
    def save_license(self, session: Session, license_details: dict) -> None:
        """
        Saves a license using an "upsert" (update or insert) strategy.
        This prevents UNIQUE constraint errors if the key already exists from
        a previously interrupted setup.
        """
        license_key = license_details.get("license_key")
        if not license_key:
            # This should not happen if the logic layer is working, but it's a good safeguard.
            raise ValueError("License details dictionary must contain a 'license_key'")

        # Step 1: Query for an existing license with the same key.
        existing_license = session.query(LicenseModel).filter_by(license_key=license_key).first()

        if existing_license:
            # Step 2a: If it exists, update its attributes with the new details.
            print(f"License key '{license_key}' already exists. Updating details.")
            for key, value in license_details.items():
                setattr(existing_license, key, value)
        else:
            # Step 2b: If it does not exist, create a new LicenseModel instance and add it.
            print(f"License key '{license_key}' not found. Creating new record.")
            new_license = LicenseModel(**license_details)
            session.add(new_license)

        # Step 3: Commit the transaction (either the update or the insert).
        session.commit()

    def save_translation_office(self, session: Session, office_dto: TranslationOfficeDTO, license_key: str) -> None:
        """
        Saves the translation office data using an "upsert" strategy
        to prevent errors on interrupted setups or when using the back button.
        """
        # Step 1: Query for an existing office linked to this license key.
        existing_office = session.query(TranslationOfficeDataModel).filter_by(license_key=license_key).first()

        office_data = office_dto.__dict__

        if existing_office:
            # Step 2a: If it exists, update its attributes with the new DTO data.
            print(f"Office for license key '{license_key}' already exists. Updating details.")
            for key, value in office_data.items():
                setattr(existing_office, key, value)
        else:
            # Step 2b: If it does not exist, add the license_key to the data
            # and create a new object.
            print(f"Office for license key '{license_key}' not found. Creating new record.")
            office_data['license_key'] = license_key
            new_office = TranslationOfficeDataModel(**office_data)
            session.add(new_office)

        # Step 3: Commit the transaction (either the update or the insert).
        session.commit()

    def save_admin_user_and_profile(self, session: Session, user_dto: AdminUserDTO,
                                    profile_dto: AdminProfileDTO | None) -> None:
        """
        Saves the admin user, profile, and security questions,
        using bcrypt for all hashing to match the login system.
        """
        # --- STEP 2: Use bcrypt to hash the password ---
        password_hash = bcrypt.hashpw(user_dto.password.encode('utf-8'), bcrypt.gensalt())

        new_user = UsersModel(
            username=user_dto.username,
            password_hash=password_hash,
            role='admin'
        )

        if profile_dto and profile_dto.full_name:
            new_profile = UserProfileModel(
                full_name=profile_dto.full_name,
                national_id=profile_dto.national_id,
                role_fa=profile_dto.role_fa,
                email=profile_dto.email,
                phone=profile_dto.phone
            )
            new_user.user_profile = new_profile

        session.add(new_user)
        session.flush()  # Get the new_user.id

        # --- STEP 3: Use bcrypt to hash the security answers for consistency ---
        answer1_hash = bcrypt.hashpw(user_dto.security_answer_1.encode('utf-8'), bcrypt.gensalt())
        question1 = SecurityQuestionModel(
            user_id=new_user.id,
            question=user_dto.security_question_1,
            answer_hash=answer1_hash
        )

        answer2_hash = bcrypt.hashpw(user_dto.security_answer_2.encode('utf-8'), bcrypt.gensalt())
        question2 = SecurityQuestionModel(
            user_id=new_user.id,
            question=user_dto.security_question_2,
            answer_hash=answer2_hash
        )

        session.add(question1)
        session.add(question2)

        session.commit()
